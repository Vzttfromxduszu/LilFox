from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from config.service_registry import ServiceRegistry
from core.service_discovery import ServiceDiscovery
from core.load_balancer import LoadBalancer
from core.router import RequestRouter
from core.auth import AuthManager
from core.rate_limiter import RateLimiter
from core.circuit_breaker import CircuitBreakerManager
from core.transformer import RequestTransformer, ResponseTransformer
from monitoring.logger import get_logger
from monitoring.metrics import MetricsCollector
from monitoring.health_check import HealthChecker

logger = get_logger(__name__)

registry = None
discovery = None
load_balancer = None
router = None
auth_manager = None
rate_limiter = None
circuit_breaker_manager = None
request_transformer = None
response_transformer = None
metrics_collector = None
health_checker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global registry, discovery, load_balancer, router, auth_manager, rate_limiter
    global circuit_breaker_manager, request_transformer, response_transformer
    global metrics_collector, health_checker
    
    logger.info("Starting LilFox API Gateway...")
    
    try:
        registry = ServiceRegistry()
        discovery = ServiceDiscovery(registry)
        load_balancer = LoadBalancer()
        router = RequestRouter(discovery, load_balancer)
        auth_manager = AuthManager()
        rate_limiter = RateLimiter()
        circuit_breaker_manager = CircuitBreakerManager()
        request_transformer = RequestTransformer()
        response_transformer = ResponseTransformer()
        metrics_collector = MetricsCollector()
        health_checker = HealthChecker()
        
        for service_name, service_config in settings.DEFAULT_BACKENDS.items():
            await registry.register_service(
                name=service_name,
                url=service_config["url"],
                health_check=service_config["health_check"],
                weight=service_config["weight"]
            )
        
        await registry.start_health_check(settings.SERVICE_HEALTH_CHECK_INTERVAL)
        
        await health_checker.start_periodic_checks()
        
        logger.info("LilFox API Gateway started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error starting gateway: {e}")
        raise
    finally:
        logger.info("Shutting down LilFox API Gateway...")
        
        if registry:
            await registry.stop_health_check()
        
        if health_checker:
            await health_checker.stop_periodic_checks()
        
        if router:
            await router.close()
        
        logger.info("LilFox API Gateway stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    from utils.helpers import generate_request_id, extract_client_ip, Timer
    
    request_id = generate_request_id()
    request.state.request_id = request_id
    request.state.client_ip = extract_client_ip(request)
    request.state.start_time = Timer()
    request.state.start_time.start()
    
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {request.state.client_ip}"
    )
    
    try:
        if settings.AUTH_ENABLED:
            auth_result = await auth_manager.authenticate_request(request)
            if not auth_result:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "request_id": request_id
                    }
                )
            request.state.user = auth_result
        
        if settings.RATE_LIMIT_ENABLED:
            identifier = request.state.client_ip
            if not await rate_limiter.is_allowed(identifier):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too many requests",
                        "request_id": request_id
                    }
                )
        
        response = await call_next(request)
        
        duration = request.state.start_time.elapsed()
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"
        
        logger.info(
            f"Request {request_id} completed: {response.status_code} "
            f"in {duration:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Request {request_id} failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": request_id
            }
        )


@app.get("/health")
async def health_check():
    """健康检查"""
    if health_checker:
        overall_status = await health_checker.get_overall_status()
        return overall_status
    return {"status": "healthy"}


@app.get("/metrics")
async def get_metrics():
    """获取指标"""
    if metrics_collector:
        return metrics_collector.get_all_metrics()
    return {}


@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """获取Prometheus格式指标"""
    if metrics_collector:
        return Response(
            content=metrics_collector.export_prometheus(),
            media_type="text/plain"
        )
    return Response(content="", media_type="text/plain")


@app.get("/services")
async def list_services():
    """列出所有服务"""
    if discovery:
        return await discovery.get_all_services_status()
    return {}


@app.get("/services/{service_name}")
async def get_service_status(service_name: str):
    """获取服务状态"""
    if discovery:
        return await discovery.get_service_status(service_name)
    return {"service": service_name, "status": "unknown"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(request: Request, path: str):
    """代理请求到后端服务"""
    method = request.method
    
    if settings.CIRCUIT_BREAKER_ENABLED:
        service_name, _ = router._parse_path(f"/{path}")
        if service_name:
            breaker = await circuit_breaker_manager.get_breaker(service_name)
            
            async def forward_request():
                return await router.route_request(request, f"/{path}", method)
            
            try:
                return await breaker.call(forward_request)
            except Exception as e:
                from core.circuit_breaker import CircuitBreakerOpenError
                if isinstance(e, CircuitBreakerOpenError):
                    return JSONResponse(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        content={"error": "Service unavailable (circuit breaker open)"}
                    )
                raise
    else:
        return await router.route_request(request, f"/{path}", method)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.GATEWAY_HOST,
        port=settings.GATEWAY_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

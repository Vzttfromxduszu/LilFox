import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path
import signal
import httpx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from monitoring.logger import get_logger

logger = get_logger(__name__)


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes = {}
        self.services = {
            "backend": {
                "path": Path(__file__).parent.parent / "backend",
                "command": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                "health_url": "http://localhost:8000/",
                "startup_delay": 5
            },
            "model_service": {
                "path": Path(__file__).parent.parent / "model_service",
                "command": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
                "health_url": "http://localhost:8001/",
                "startup_delay": 5
            },
            "gateway": {
                "path": Path(__file__).parent,
                "command": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"],
                "health_url": "http://localhost:8080/health",
                "startup_delay": 3
            }
        }
    
    async def start_service(self, service_name: str) -> bool:
        """启动服务"""
        if service_name not in self.services:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        service = self.services[service_name]
        
        if service_name in self.processes:
            logger.warning(f"Service {service_name} is already running")
            return True
        
        logger.info(f"Starting service: {service_name}")
        
        try:
            process = subprocess.Popen(
                service["command"],
                cwd=str(service["path"]),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[service_name] = process
            
            logger.info(f"Service {service_name} started with PID: {process.pid}")
            
            await asyncio.sleep(service["startup_delay"])
            
            if await self.check_service_health(service_name):
                logger.info(f"Service {service_name} is healthy")
                return True
            else:
                logger.warning(f"Service {service_name} health check failed")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            return False
    
    async def check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        health_url = service["health_url"]
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                return response.status_code < 500
        except Exception as e:
            logger.warning(f"Health check failed for {service_name}: {e}")
            return False
    
    async def start_all(self):
        """启动所有服务"""
        logger.info("Starting all services...")
        
        services_order = ["backend", "model_service", "gateway"]
        
        for service_name in services_order:
            await self.start_service(service_name)
            await asyncio.sleep(2)
        
        logger.info("All services started")
        
        print("\n" + "="*60)
        print("🚀 All services started successfully!")
        print("="*60)
        print("\n📊 Service Status:")
        print("-" * 60)
        
        for service_name in services_order:
            health = await self.check_service_health(service_name)
            status = "✅ Healthy" if health else "❌ Unhealthy"
            service = self.services[service_name]
            print(f"  {service_name:15} - {status:15} ({service['health_url']})")
        
        print("-" * 60)
        print("\n🌐 Access URLs:")
        print(f"  Gateway:    http://localhost:8080")
        print(f"  Backend:    http://localhost:8000")
        print(f"  Model Service: http://localhost:8001")
        print("\n💡 Press Ctrl+C to stop all services")
        print("="*60 + "\n")
    
    async def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        if service_name not in self.processes:
            logger.warning(f"Service {service_name} is not running")
            return True
        
        process = self.processes[service_name]
        
        logger.info(f"Stopping service: {service_name}")
        
        try:
            process.terminate()
            
            try:
                process.wait(timeout=10)
                logger.info(f"Service {service_name} stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Service {service_name} did not stop gracefully, killing...")
                process.kill()
                process.wait()
                logger.info(f"Service {service_name} killed")
            
            del self.processes[service_name]
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    async def stop_all(self):
        """停止所有服务"""
        logger.info("Stopping all services...")
        
        services_order = list(self.processes.keys())
        
        for service_name in reversed(services_order):
            await self.stop_service(service_name)
            await asyncio.sleep(1)
        
        logger.info("All services stopped")
    
    async def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        logger.info(f"Restarting service: {service_name}")
        
        await self.stop_service(service_name)
        await asyncio.sleep(2)
        return await self.start_service(service_name)
    
    async def get_service_status(self) -> dict:
        """获取所有服务状态"""
        status = {}
        
        for service_name, service in self.services.items():
            is_running = service_name in self.processes
            is_healthy = await self.check_service_health(service_name) if is_running else False
            
            status[service_name] = {
                "running": is_running,
                "healthy": is_healthy,
                "pid": self.processes[service_name].pid if is_running else None,
                "url": service["health_url"]
            }
        
        return status
    
    async def monitor_services(self, interval: int = 30):
        """监控服务"""
        logger.info(f"Starting service monitoring (interval: {interval}s)")
        
        try:
            while True:
                await asyncio.sleep(interval)
                
                for service_name in self.processes.keys():
                    if not await self.check_service_health(service_name):
                        logger.warning(f"Service {service_name} is unhealthy, attempting restart...")
                        await self.restart_service(service_name)
                        
        except asyncio.CancelledError:
            logger.info("Service monitoring stopped")


async def main():
    """主函数"""
    manager = ServiceManager()
    
    try:
        await manager.start_all()
        
        monitor_task = asyncio.create_task(manager.monitor_services())
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await manager.stop_all()


if __name__ == "__main__":
    asyncio.run(main())

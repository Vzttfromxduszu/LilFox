from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.routes import router
from src.routes.beer import router as beer_router
import uvicorn


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="大模型交互服务API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(beer_router, prefix=f"{settings.API_PREFIX}/beer", tags=["精酿啤酒推荐"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to LilFox Model Service",
        "version": settings.VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
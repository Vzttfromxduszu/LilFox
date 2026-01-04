from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import auth_router
from src.utils.exceptions import add_exception_handlers

app = FastAPI(
    title="User Authentication System",
    description="A complete user authentication system with FastAPI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# Add custom exception handlers
add_exception_handlers(app)

@app.get("/")
def root():
    return {"message": "User Authentication System API", "version": "1.0.0"}

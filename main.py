from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Register all ORM models BEFORE init_db()
from db.models import User, Project, InputForm  # noqa: F401
from db.database import init_db
from api.chat_router import router as chat_router
from api.projects_router import router as projects_router
from auth.auth_router import router as auth_router

from dotenv import load_dotenv
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅ Database initialized")
    yield
    print("🛑 Shutting down")


app = FastAPI(
    title="System Designer Assistant",
    description="AI-powered Java Spring Boot system design assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "System Designer Assistant"}
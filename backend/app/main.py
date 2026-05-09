from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: ensure all models registered
from app.api import auth, users, machines, scenarios, prompts, skills, deploy, plans, monitor, agent

app = FastAPI(title="OpenClaw Center", description="OpenClaw Enterprise Management Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(machines.router, prefix="/api/machines", tags=["Machines"])
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenarios"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["Prompts"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(deploy.router, prefix="/api/deploy-tasks", tags=["Deploy"])
app.include_router(plans.router, prefix="/api/coding-plans", tags=["Plans"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitor"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "openclaw-center"}

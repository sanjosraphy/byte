"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import init_db
from app.api import (
    auth, users, health, agents, communication,
    permissions, consent, audit, field_permissions, demo, llm
)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="AI² Backend",
    description="Privacy-First Network of Personal AI Agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)
app.include_router(communication.router)
app.include_router(permissions.router)
app.include_router(consent.router)
app.include_router(audit.router)
app.include_router(field_permissions.router)
app.include_router(demo.router)
app.include_router(llm.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI² Backend - Privacy-First Network of Personal AI Agents",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "phases": {
            "phase_2": "✅ Backend foundation, Users A/B, Agents A/B",
            "phase_3": "✅ Agent-to-Agent communication",
            "phase_4": "✅ Permission engine with ALLOW/DENY logic",
            "phase_5": "✅ Granular field-level permissions",
            "phase_10": "✅ Demo scenarios (movie night, project coordination)",
            "phase_12": "✅ LLM integration for AI understanding"
        },
        "endpoints": {
            "demo": "/api/demo/run/movie-night, /api/demo/run/project-coordination",
            "llm": "/api/llm/understand, /api/llm/plan-requests, /api/llm/reason",
            "permissions": "/api/permissions/*, /api/field-permissions/*",
            "audit": "/api/audit/logs/my-data, /api/audit/logs/my-requests, /api/audit/summary",
            "communication": "/api/communication/request, /api/communication/requests/incoming",
            "docs": "Visit /docs for interactive API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )

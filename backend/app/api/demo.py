"""Demo scenarios API routes for Phase 10."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.schema import User
from app.database.demo_schema import DemoScenario, DemoResult
from app.middleware.auth import get_current_user
from app.services.demo_service import DemoService
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any, Dict


class DemoScenarioResponse(BaseModel):
    """Demo scenario response."""
    id: int
    scenario_name: str
    description: str
    initiating_user_name: str
    target_user_name: str
    initial_request: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DemoResultResponse(BaseModel):
    """Demo result response."""
    id: int
    step_number: int
    step_description: str
    data_requested: Dict[str, Any]
    permission_status: str
    user_decision: Optional[str]
    data_shared: Optional[Dict[str, Any]]
    agent_reasoning: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/run/movie-night", response_model=DemoScenarioResponse)
async def run_movie_night_demo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    target_user_id: Optional[int] = None
):
    """Run the movie night demo scenario.

    Default: current_user is User A, uses User B (ID=2 if current is 1, else 1)
    Optional: specify target_user_id explicitly
    """
    try:
        # Determine target user
        if target_user_id:
            if target_user_id == current_user.id:
                raise ValueError("Cannot run demo with yourself")
            target_user = db.query(User).filter(User.id == target_user_id).first()
            if not target_user:
                raise ValueError(f"User {target_user_id} not found")
        else:
            # Default: if current_user is alice (1), use bob (2), otherwise alice
            target_user_id = 2 if current_user.id == 1 else 1
            target_user = db.query(User).filter(User.id == target_user_id).first()

        scenario = DemoService.run_movie_night_demo(
            db,
            current_user.id,
            target_user.id
        )

        return DemoScenarioResponse(
            id=scenario.id,
            scenario_name=scenario.scenario_name,
            description=scenario.description,
            initiating_user_name=current_user.full_name,
            target_user_name=target_user.full_name,
            initial_request=scenario.initial_request,
            status=scenario.status,
            created_at=scenario.created_at,
            completed_at=scenario.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/run/project-coordination", response_model=DemoScenarioResponse)
async def run_project_coordination_demo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    target_user_id: Optional[int] = None
):
    """Run the project coordination demo scenario."""
    try:
        if target_user_id:
            if target_user_id == current_user.id:
                raise ValueError("Cannot run demo with yourself")
            target_user = db.query(User).filter(User.id == target_user_id).first()
            if not target_user:
                raise ValueError(f"User {target_user_id} not found")
        else:
            target_user_id = 2 if current_user.id == 1 else 1
            target_user = db.query(User).filter(User.id == target_user_id).first()

        scenario = DemoService.run_project_coordination_demo(
            db,
            current_user.id,
            target_user.id
        )

        return DemoScenarioResponse(
            id=scenario.id,
            scenario_name=scenario.scenario_name,
            description=scenario.description,
            initiating_user_name=current_user.full_name,
            target_user_name=target_user.full_name,
            initial_request=scenario.initial_request,
            status=scenario.status,
            created_at=scenario.created_at,
            completed_at=scenario.completed_at
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/scenario/{scenario_id}", response_model=DemoScenarioResponse)
async def get_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get demo scenario details."""
    try:
        scenario = db.query(DemoScenario).filter(
            DemoScenario.id == scenario_id
        ).first()

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )

        initiating_user = db.query(User).filter(
            User.id == scenario.initiating_user_id
        ).first()
        target_user = db.query(User).filter(
            User.id == scenario.target_user_id
        ).first()

        return DemoScenarioResponse(
            id=scenario.id,
            scenario_name=scenario.scenario_name,
            description=scenario.description,
            initiating_user_name=initiating_user.full_name if initiating_user else "Unknown",
            target_user_name=target_user.full_name if target_user else "Unknown",
            initial_request=scenario.initial_request,
            status=scenario.status,
            created_at=scenario.created_at,
            completed_at=scenario.completed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/scenario/{scenario_id}/results", response_model=List[DemoResultResponse])
async def get_scenario_results(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all results/steps for a demo scenario.

    Returns the complete execution log showing:
    - What data was requested
    - Permission decisions
    - What data was actually shared
    - Agent reasoning
    """
    try:
        scenario = db.query(DemoScenario).filter(
            DemoScenario.id == scenario_id
        ).first()

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scenario not found"
            )

        results = DemoService.get_scenario_results(db, scenario_id)

        return [
            DemoResultResponse(
                id=r.id,
                step_number=r.step_number,
                step_description=r.step_description,
                data_requested=r.data_requested,
                permission_status=r.permission_status,
                user_decision=r.user_decision,
                data_shared=r.data_shared,
                agent_reasoning=r.agent_reasoning,
                timestamp=r.timestamp
            )
            for r in results
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

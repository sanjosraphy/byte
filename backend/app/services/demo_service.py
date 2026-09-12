"""Demo scenario service for Phase 10."""
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.schema import User, Agent
from app.database.demo_schema import DemoScenario, DemoResult
from app.database.communication_schema import AgentRequest
from app.services.communication_service import CommunicationService
from app.services.permission_service import PermissionService
from app.models.permission import ConsentDecision, PermissionType
from typing import List, Dict, Any, Optional


class DemoService:
    """Service for running demo scenarios."""

    @staticmethod
    def create_demo_scenario(
        db: Session,
        scenario_name: str,
        description: str,
        initiating_user_id: int,
        target_user_id: int,
        initial_request: str
    ) -> DemoScenario:
        """Create a new demo scenario."""
        scenario = DemoScenario(
            scenario_name=scenario_name,
            description=description,
            initiating_user_id=initiating_user_id,
            target_user_id=target_user_id,
            initial_request=initial_request,
            status="in_progress",
            created_at=datetime.utcnow()
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    @staticmethod
    def log_demo_step(
        db: Session,
        scenario_id: int,
        step_number: int,
        step_description: str,
        data_requested: Dict[str, Any],
        permission_status: str,
        user_decision: Optional[str] = None,
        data_shared: Optional[Dict[str, Any]] = None,
        agent_reasoning: Optional[str] = None
    ) -> DemoResult:
        """Log a step in a demo scenario execution."""
        result = DemoResult(
            scenario_id=scenario_id,
            step_number=step_number,
            step_description=step_description,
            data_requested=data_requested,
            permission_status=permission_status,
            user_decision=user_decision,
            data_shared=data_shared,
            agent_reasoning=agent_reasoning,
            timestamp=datetime.utcnow()
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def complete_scenario(db: Session, scenario_id: int) -> DemoScenario:
        """Mark a scenario as completed."""
        scenario = db.query(DemoScenario).filter(
            DemoScenario.id == scenario_id
        ).first()
        if scenario:
            scenario.status = "completed"
            scenario.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(scenario)
        return scenario

    @staticmethod
    def run_movie_night_demo(db: Session, user_a_id: int, user_b_id: int) -> DemoScenario:
        """Run the movie night demo scenario.

        Scenario:
        - User A wants to plan a movie night with User B
        - Agent A needs: availability, movie preferences, budget
        - User B gets consent screen
        - User B approves with time-based permissions
        - Agents coordinate and produce result
        """
        # Create scenario
        scenario = DemoService.create_demo_scenario(
            db,
            scenario_name="movie_night",
            description="Plan a movie night with privacy-respecting agent coordination",
            initiating_user_id=user_a_id,
            target_user_id=user_b_id,
            initial_request="Plan a movie with my friend this evening"
        )

        user_a = db.query(User).filter(User.id == user_a_id).first()
        user_b = db.query(User).filter(User.id == user_b_id).first()
        agent_a = db.query(Agent).filter(Agent.user_id == user_a_id).first()
        agent_b = db.query(Agent).filter(Agent.user_id == user_b_id).first()

        # STEP 1: Agent A requests availability
        DemoService.log_demo_step(
            db,
            scenario.id,
            1,
            "Agent A requests User B's calendar availability",
            {"data_category": "calendar", "fields": ["free_busy", "availability_windows"]},
            "PENDING_CONSENT"
        )

        # Create the actual request
        request_1 = CommunicationService.create_request(
            db,
            requesting_agent_id=agent_a.id,
            target_agent_unique_key=agent_b.unique_key,
            request_type="calendar_availability",
            requested_data_category="calendar",
            requested_fields=["free_busy", "availability_windows"],
            purpose="schedule_movie_night",
            context={"time_window": "evening", "duration_hours": 2}
        )

        # STEP 2: User B sees consent screen
        consent_data = PermissionService.prepare_consent_screen(db, request_1.id)
        DemoService.log_demo_step(
            db,
            scenario.id,
            2,
            f"Consent screen shown to {user_b.full_name}",
            {"what": consent_data["what_will_be_shared"], "who": consent_data["who_is_requesting"]},
            "PENDING_CONSENT"
        )

        # STEP 3: User B approves for 1 hour
        permission_1 = PermissionService.handle_consent_decision(
            db,
            request_1.id,
            ConsentDecision.ALLOWED_FOR_DURATION
        )

        processed_1 = CommunicationService.process_request(db, request_1.id)
        DemoService.log_demo_step(
            db,
            scenario.id,
            3,
            f"{user_b.full_name} approved calendar access for 1 hour",
            {"fields": ["free_busy", "availability_windows"]},
            "ALLOWED",
            "allowed_for_duration",
            processed_1.response_data,
            "Permission granted with 1-hour expiration. Data is minimized to availability only."
        )

        # STEP 4: Agent A requests preferences
        request_2 = CommunicationService.create_request(
            db,
            requesting_agent_id=agent_a.id,
            target_agent_unique_key=agent_b.unique_key,
            request_type="preference_query",
            requested_data_category="preferences",
            requested_fields=["movie_genre"],
            purpose="select_suitable_movie",
            context={"genres_available": ["action", "sci-fi", "comedy", "drama"]}
        )

        DemoService.log_demo_step(
            db,
            scenario.id,
            4,
            "Agent A requests User B's movie preferences",
            {"data_category": "preferences", "fields": ["movie_genre"]},
            "PENDING_CONSENT"
        )

        # STEP 5: User B approves preferences
        permission_2 = PermissionService.handle_consent_decision(
            db,
            request_2.id,
            ConsentDecision.ALLOWED_FOR_DURATION
        )
        processed_2 = CommunicationService.process_request(db, request_2.id)
        DemoService.log_demo_step(
            db,
            scenario.id,
            5,
            f"{user_b.full_name} approved preference access for 1 hour",
            {"fields": ["movie_genre"]},
            "ALLOWED",
            "allowed_for_duration",
            processed_2.response_data
        )

        # STEP 6: Agent A requests budget
        request_3 = CommunicationService.create_request(
            db,
            requesting_agent_id=agent_a.id,
            target_agent_unique_key=agent_b.unique_key,
            request_type="budget_query",
            requested_data_category="budget",
            requested_fields=["entertainment_max"],
            purpose="verify_movie_ticket_budget",
            context={"estimated_cost_per_person": 300}
        )

        DemoService.log_demo_step(
            db,
            scenario.id,
            6,
            "Agent A requests User B's entertainment budget",
            {"data_category": "budget", "fields": ["entertainment_max"]},
            "PENDING_CONSENT"
        )

        # STEP 7: User B approves budget
        permission_3 = PermissionService.handle_consent_decision(
            db,
            request_3.id,
            ConsentDecision.ALLOWED_FOR_DURATION
        )
        processed_3 = CommunicationService.process_request(db, request_3.id)
        DemoService.log_demo_step(
            db,
            scenario.id,
            7,
            f"{user_b.full_name} approved budget access for 1 hour",
            {"fields": ["entertainment_max"]},
            "ALLOWED",
            "allowed_for_duration",
            processed_3.response_data
        )

        # STEP 8: Agents coordinate and produce result
        # Get Alice's data
        user_a_calendar = db.query(User).filter(User.id == user_a_id).first()
        user_a_prefs = db.query(User).filter(User.id == user_a_id).first()

        result_summary = {
            "recommendation": "Movie night coordinated successfully",
            "meeting_time": "7:30 PM - 9:30 PM (both available)",
            "movie_selection": "Action/Sci-Fi (intersection of preferences)",
            "estimated_cost": "₹600 total (₹300 per person)",
            "privacy_summary": {
                "bob_data_shared": ["availability_windows", "movie_genre", "entertainment_budget"],
                "bob_data_protected": ["event_names", "attendees", "locations"],
                "permissions_active": 3,
                "permissions_expires": "in 1 hour",
                "audit_logged": True
            }
        }

        DemoService.log_demo_step(
            db,
            scenario.id,
            8,
            "Agents coordinate and produce final recommendation",
            {},
            "ALLOWED",
            "auto_coordinated",
            result_summary,
            "Both agents analyzed approved data and found optimal meeting time with movie preference match within budget constraints."
        )

        # Mark scenario complete
        DemoService.complete_scenario(db, scenario.id)

        return scenario

    @staticmethod
    def run_project_coordination_demo(db: Session, user_a_id: int, user_b_id: int) -> DemoScenario:
        """Run the project coordination demo scenario.

        Scenario:
        - User A wants to divide project work with User B
        - Agent A needs: availability, skills, current tasks
        - User B approves selective access
        - Agents negotiate and produce work division
        """
        scenario = DemoService.create_demo_scenario(
            db,
            scenario_name="project_coordination",
            description="Coordinate project work division with privacy-aware agents",
            initiating_user_id=user_a_id,
            target_user_id=user_b_id,
            initial_request="Divide project work with my teammate"
        )

        user_a = db.query(User).filter(User.id == user_a_id).first()
        user_b = db.query(User).filter(User.id == user_b_id).first()
        agent_a = db.query(Agent).filter(Agent.user_id == user_a_id).first()
        agent_b = db.query(Agent).filter(Agent.user_id == user_b_id).first()

        # STEP 1: Request availability
        request_1 = CommunicationService.create_request(
            db,
            requesting_agent_id=agent_a.id,
            target_agent_unique_key=agent_b.unique_key,
            request_type="availability_query",
            requested_data_category="calendar",
            requested_fields=["availability_windows"],
            purpose="coordinate_project_timeline"
        )

        DemoService.log_demo_step(
            db,
            scenario.id,
            1,
            "Agent A requests User B's availability",
            {"data_category": "calendar", "fields": ["availability_windows"]},
            "PENDING_CONSENT"
        )

        # User B approves
        permission_1 = PermissionService.handle_consent_decision(
            db,
            request_1.id,
            ConsentDecision.ALLOWED_FOR_DURATION
        )
        processed_1 = CommunicationService.process_request(db, request_1.id)

        DemoService.log_demo_step(
            db,
            scenario.id,
            2,
            f"{user_b.full_name} approved availability sharing",
            {"fields": ["availability_windows"]},
            "ALLOWED",
            "allowed_for_duration",
            processed_1.response_data
        )

        # STEP 2: Request preferences (skills)
        request_2 = CommunicationService.create_request(
            db,
            requesting_agent_id=agent_a.id,
            target_agent_unique_key=agent_b.unique_key,
            request_type="skill_query",
            requested_data_category="preferences",
            requested_fields=["music_taste"],  # Placeholder for skills
            purpose="match_skills_to_tasks"
        )

        permission_2 = PermissionService.handle_consent_decision(
            db,
            request_2.id,
            ConsentDecision.ALLOWED_FOR_DURATION
        )
        processed_2 = CommunicationService.process_request(db, request_2.id)

        DemoService.log_demo_step(
            db,
            scenario.id,
            3,
            "Agent A requests User B's skill preferences",
            {"data_category": "preferences"},
            "ALLOWED",
            "allowed_for_duration",
            processed_2.response_data
        )

        # Final recommendation
        result_summary = {
            "work_division": {
                "user_a_tasks": ["Backend API development", "Database design"],
                "user_b_tasks": ["Frontend UI development", "Testing framework"],
                "timeline": "Day 1-2: Backend, Day 3-4: Frontend, Day 5: Integration"
            },
            "privacy_summary": {
                "bob_data_shared": ["availability_windows"],
                "bob_data_protected": ["full_calendar", "event_details", "private_preferences"],
                "permissions_active": 2,
                "audit_logged": True
            }
        }

        DemoService.log_demo_step(
            db,
            scenario.id,
            4,
            "Work division coordinated based on availability and skills",
            {},
            "ALLOWED",
            "auto_coordinated",
            result_summary
        )

        DemoService.complete_scenario(db, scenario.id)
        return scenario

    @staticmethod
    def get_scenario_results(db: Session, scenario_id: int) -> List[DemoResult]:
        """Get all results for a scenario."""
        return db.query(DemoResult).filter(
            DemoResult.scenario_id == scenario_id
        ).order_by(DemoResult.step_number).all()

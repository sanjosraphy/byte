"""LLM integration service for Phase 12."""
import os
from typing import Optional, List, Dict, Any


class LLMService:
    """Service for integrating with LLM APIs.

    Currently supports:
    - Ollama (local, free)
    - Groq (free tier with generous limits)
    - OpenRouter (pay-as-you-go)

    The LLM is used ONLY for:
    1. Understanding user requests
    2. Planning what information is needed
    3. Generating structured requests
    4. Reasoning over approved data

    The LLM NEVER makes authorization decisions.
    """

    @staticmethod
    def get_llm_provider() -> str:
        """Get configured LLM provider."""
        return os.getenv("LLM_PROVIDER", "groq")

    @staticmethod
    def understand_user_request(user_request: str) -> Dict[str, Any]:
        """Use LLM to understand what user is asking for.

        Args:
            user_request: Natural language request from user

        Returns:
            Structured understanding of request
        """
        # This would call the LLM in Phase 12
        # For now, return a structured response
        return {
            "intent": "plan_social_activity",
            "activity_type": "movie_night",
            "participants": ["friend"],
            "timeframe": "this_evening",
            "required_information": ["availability", "preferences", "budget"]
        }

    @staticmethod
    def plan_data_requests(
        user_request: str,
        understanding: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate structured data requests based on user intent.

        Args:
            user_request: Original request
            understanding: LLM's understanding of intent

        Returns:
            List of data requests needed
        """
        # This would call the LLM to generate requests
        return [
            {
                "data_category": "calendar",
                "fields": ["free_busy", "availability_windows"],
                "purpose": "find_available_time",
                "suggested_permission_type": "one_hour"
            },
            {
                "data_category": "preferences",
                "fields": ["movie_genre"],
                "purpose": "select_suitable_movie",
                "suggested_permission_type": "one_hour"
            },
            {
                "data_category": "budget",
                "fields": ["entertainment_max"],
                "purpose": "verify_affordability",
                "suggested_permission_type": "one_hour"
            }
        ]

    @staticmethod
    def reason_over_data(
        approved_data: Dict[str, Any],
        user_context: Dict[str, Any],
        task: str
    ) -> str:
        """Use LLM to reason over approved data and produce recommendations.

        Args:
            approved_data: Data that was approved by other user
            user_context: Current user's information
            task: What task to perform

        Returns:
            LLM's reasoning and recommendation
        """
        # This would call the LLM to reason over data
        return f"Based on available data, recommended action: {task}"

    @staticmethod
    def generate_request_explanation(request_data: Dict[str, Any]) -> str:
        """Generate human-readable explanation of what data is being requested.

        Args:
            request_data: The data request

        Returns:
            Human-readable explanation
        """
        return (
            f"Your agent needs your {request_data.get('data_category', 'data')} "
            f"({', '.join(request_data.get('fields', []))}) "
            f"to {request_data.get('purpose', 'complete a task')}."
        )

    @staticmethod
    def validate_request_purpose(
        data_category: str,
        requested_fields: List[str],
        stated_purpose: str
    ) -> bool:
        """Validate that stated purpose aligns with data being requested.

        This is a safety check to prevent agents from requesting unnecessary data.

        Args:
            data_category: What category of data
            requested_fields: Specific fields
            stated_purpose: Why it's being requested

        Returns:
            True if purpose seems legitimate
        """
        # In Phase 12, this would call the LLM to validate
        # For now, basic validation
        if "schedule" in stated_purpose or "meeting" in stated_purpose:
            if data_category == "calendar":
                return True
        if "preference" in stated_purpose or "like" in stated_purpose:
            if data_category == "preferences":
                return True
        if "budget" in stated_purpose or "cost" in stated_purpose:
            if data_category == "budget":
                return True
        return False

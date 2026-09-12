"""Field-level permission service."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.schema import Agent, User
from app.database.field_permission_schema import FieldLevelPermission
from app.models.field_permission import FieldPermissionType
from typing import Optional, List, Dict


class FieldPermissionService:
    """Service for managing granular field-level permissions."""

    # Define all available fields per category
    AVAILABLE_FIELDS = {
        "calendar": {
            "free_busy": {
                "display_name": "Free/Busy Status",
                "description": "Only shows if user is busy or free, no event details",
                "sensitivity_level": 1,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "availability_windows": {
                "display_name": "Availability Windows",
                "description": "Time periods when user is available",
                "sensitivity_level": 1,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "event_names": {
                "display_name": "Event Titles",
                "description": "Names of calendar events (without details)",
                "sensitivity_level": 2,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "event_descriptions": {
                "display_name": "Event Descriptions",
                "description": "Detailed descriptions of calendar events",
                "sensitivity_level": 3,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "event_attendees": {
                "display_name": "Event Attendees",
                "description": "Who else is invited to events",
                "sensitivity_level": 3,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "event_locations": {
                "display_name": "Event Locations",
                "description": "Where events are taking place",
                "sensitivity_level": 2,
                "default_permission": FieldPermissionType.HIDDEN
            }
        },
        "location": {
            "left_home": {
                "display_name": "Left Home Status",
                "description": "Simple yes/no: has user left home?",
                "sensitivity_level": 1,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "location_name": {
                "display_name": "Location Name",
                "description": "General location (e.g., 'Office', 'Home', 'Downtown')",
                "sensitivity_level": 2,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "approximate_area": {
                "display_name": "Approximate Area",
                "description": "General area (e.g., '5km radius')",
                "sensitivity_level": 2,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "city": {
                "display_name": "City",
                "description": "User's city",
                "sensitivity_level": 2,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "exact_gps": {
                "display_name": "Exact GPS Coordinates",
                "description": "Precise latitude and longitude",
                "sensitivity_level": 5,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "location_history": {
                "display_name": "Location History",
                "description": "Places user has visited",
                "sensitivity_level": 5,
                "default_permission": FieldPermissionType.HIDDEN
            }
        },
        "preferences": {
            "movie_genre": {
                "display_name": "Movie Preferences",
                "description": "Preferred movie genres",
                "sensitivity_level": 1,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "music_taste": {
                "display_name": "Music Taste",
                "description": "Preferred music genres",
                "sensitivity_level": 1,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "cuisine": {
                "display_name": "Cuisine Preferences",
                "description": "Preferred types of food",
                "sensitivity_level": 1,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "dietary_restrictions": {
                "display_name": "Dietary Restrictions",
                "description": "Allergies and dietary limitations (health sensitive)",
                "sensitivity_level": 4,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "travel_interests": {
                "display_name": "Travel Interests",
                "description": "Preferred travel destinations",
                "sensitivity_level": 2,
                "default_permission": FieldPermissionType.HIDDEN
            }
        },
        "budget": {
            "entertainment_max": {
                "display_name": "Entertainment Budget",
                "description": "Maximum spending on entertainment",
                "sensitivity_level": 3,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "travel_max": {
                "display_name": "Travel Budget",
                "description": "Maximum spending on travel",
                "sensitivity_level": 3,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "food_max": {
                "display_name": "Food Budget",
                "description": "Maximum spending on meals",
                "sensitivity_level": 3,
                "default_permission": FieldPermissionType.HIDDEN
            },
            "total_spending_limit": {
                "display_name": "Total Spending Limit",
                "description": "Overall budget ceiling (very sensitive)",
                "sensitivity_level": 4,
                "default_permission": FieldPermissionType.HIDDEN
            }
        }
    }

    # Predefined permission templates
    TEMPLATES = {
        "meeting_scheduling": {
            "name": "Meeting Scheduling",
            "description": "Share only free/busy times to find meeting slots",
            "data_category": "calendar",
            "fields": {
                "free_busy": FieldPermissionType.ACCESSIBLE,
                "availability_windows": FieldPermissionType.ACCESSIBLE,
                "event_names": FieldPermissionType.HIDDEN,
                "event_descriptions": FieldPermissionType.HIDDEN,
                "event_attendees": FieldPermissionType.HIDDEN,
                "event_locations": FieldPermissionType.HIDDEN
            },
            "recommended_duration": "one_hour",
            "use_case": "Allows agent to find common free time without revealing event details"
        },
        "social_outing": {
            "name": "Social Outing",
            "description": "Share availability and preferences for social activities",
            "data_category": "calendar+preferences",
            "fields": {
                "availability_windows": FieldPermissionType.ACCESSIBLE,
                "movie_genre": FieldPermissionType.ACCESSIBLE,
                "cuisine": FieldPermissionType.ACCESSIBLE
            },
            "recommended_duration": "one_hour",
            "use_case": "Allows agent to plan social events with preferences"
        },
        "emergency_location": {
            "name": "Emergency Location",
            "description": "Share general location for safety in emergency",
            "data_category": "location",
            "fields": {
                "left_home": FieldPermissionType.ACCESSIBLE,
                "location_name": FieldPermissionType.ACCESSIBLE,
                "city": FieldPermissionType.ACCESSIBLE,
                "exact_gps": FieldPermissionType.MINIMIZED
            },
            "recommended_duration": "one_hour",
            "use_case": "Emergency responders can find user without exact coordinates"
        },
        "trip_planning": {
            "name": "Trip Planning",
            "description": "Share budget and preferences for trip planning",
            "data_category": "budget+preferences",
            "fields": {
                "travel_max": FieldPermissionType.ACCESSIBLE,
                "travel_interests": FieldPermissionType.ACCESSIBLE,
                "cuisine": FieldPermissionType.ACCESSIBLE
            },
            "recommended_duration": "twentyfour_hours",
            "use_case": "Allows agent to plan trips within budget and preferences"
        },
        "full_transparency": {
            "name": "Full Transparency",
            "description": "Share all data with minimal restrictions",
            "data_category": "all",
            "fields": {
                # Calendar - all accessible
                "free_busy": FieldPermissionType.ACCESSIBLE,
                "availability_windows": FieldPermissionType.ACCESSIBLE,
                "event_names": FieldPermissionType.ACCESSIBLE,
                "event_descriptions": FieldPermissionType.ACCESSIBLE,
                "event_attendees": FieldPermissionType.ACCESSIBLE,
                "event_locations": FieldPermissionType.ACCESSIBLE,
                # Location - location name accessible, GPS minimized
                "location_name": FieldPermissionType.ACCESSIBLE,
                "exact_gps": FieldPermissionType.MINIMIZED,
                # Preferences - all accessible
                "movie_genre": FieldPermissionType.ACCESSIBLE,
                "music_taste": FieldPermissionType.ACCESSIBLE,
                "cuisine": FieldPermissionType.ACCESSIBLE
            },
            "recommended_duration": "twentyfour_hours",
            "use_case": "Maximum transparency for trusted agents"
        }
    }

    @staticmethod
    def grant_field_level_permission(
        db: Session,
        grantor_user_id: int,
        grantee_agent_unique_key: str,
        data_category: str,
        field_permissions: Dict[str, str],  # {"field_name": "accessible|hidden|minimized|redacted"}
        permission_type: str = "one_hour",
        custom_expiry_minutes: Optional[int] = None
    ) -> FieldLevelPermission:
        """Grant field-level permissions.

        Args:
            db: Database session
            grantor_user_id: User granting the permission
            grantee_agent_unique_key: Agent receiving permission
            data_category: Type of data (calendar, location, etc.)
            field_permissions: Dict mapping field names to permission types
            permission_type: Duration type
            custom_expiry_minutes: Custom duration in minutes

        Returns:
            FieldLevelPermission object
        """
        # Find grantee agent
        grantee_agent = db.query(Agent).filter(
            Agent.unique_key == grantee_agent_unique_key
        ).first()

        if not grantee_agent:
            raise ValueError(f"Agent '{grantee_agent_unique_key}' not found")

        # Validate fields exist
        if data_category not in FieldPermissionService.AVAILABLE_FIELDS:
            raise ValueError(f"Unknown data category: {data_category}")

        for field_name in field_permissions.keys():
            if field_name not in FieldPermissionService.AVAILABLE_FIELDS[data_category]:
                raise ValueError(
                    f"Field '{field_name}' not available in category '{data_category}'"
                )

        # Calculate expiry
        expires_at = FieldPermissionService._calculate_expiry(
            permission_type,
            custom_expiry_minutes
        )

        # Create permission
        permission = FieldLevelPermission(
            grantor_id=grantor_user_id,
            grantee_agent_id=grantee_agent.id,
            data_category=data_category,
            field_permissions=field_permissions,
            permission_type=permission_type,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_revoked=False
        )

        db.add(permission)
        db.commit()
        db.refresh(permission)

        return permission

    @staticmethod
    def _calculate_expiry(
        permission_type: str,
        custom_minutes: Optional[int] = None
    ) -> Optional[datetime]:
        """Calculate permission expiry time."""
        now = datetime.utcnow()

        expiry_map = {
            "one_time": now + timedelta(hours=1),
            "ten_minutes": now + timedelta(minutes=10),
            "one_hour": now + timedelta(hours=1),
            "twentyfour_hours": now + timedelta(hours=24),
            "until_task": now + timedelta(days=7),
        }

        if permission_type == "custom":
            if custom_minutes is None:
                raise ValueError("custom_expiry_minutes required for CUSTOM type")
            return now + timedelta(minutes=custom_minutes)

        elif permission_type == "permanent":
            return None

        return expiry_map.get(permission_type, now + timedelta(hours=1))

    @staticmethod
    def check_field_access(
        db: Session,
        grantor_user_id: int,
        grantee_agent_id: int,
        data_category: str,
        field_name: str
    ) -> Optional[str]:
        """Check if a specific field can be accessed.

        Returns:
            Permission type ("accessible", "hidden", "minimized", "redacted") or None if no permission
        """
        permission = db.query(FieldLevelPermission).filter(
            FieldLevelPermission.grantor_id == grantor_user_id,
            FieldLevelPermission.grantee_agent_id == grantee_agent_id,
            FieldLevelPermission.data_category == data_category,
            FieldLevelPermission.is_revoked == False
        ).first()

        if not permission:
            return None

        # Check expiration
        if permission.expires_at and datetime.utcnow() > permission.expires_at:
            return None

        # Get field permission
        return permission.field_permissions.get(field_name)

    @staticmethod
    def get_user_field_permissions(
        db: Session,
        user_id: int
    ) -> Dict[str, List[FieldLevelPermission]]:
        """Get all field-level permissions granted by a user.

        Returns:
            Dict mapping data categories to list of permissions
        """
        all_permissions = db.query(FieldLevelPermission).filter(
            FieldLevelPermission.grantor_id == user_id,
            FieldLevelPermission.is_revoked == False
        ).all()

        result = {}
        for perm in all_permissions:
            if perm.data_category not in result:
                result[perm.data_category] = []
            result[perm.data_category].append(perm)

        return result

    @staticmethod
    def revoke_field_permission(db: Session, permission_id: int) -> FieldLevelPermission:
        """Revoke a field-level permission."""
        permission = db.query(FieldLevelPermission).filter(
            FieldLevelPermission.id == permission_id
        ).first()

        if not permission:
            raise ValueError(f"Permission {permission_id} not found")

        permission.is_revoked = True
        permission.revoked_at = datetime.utcnow()
        db.commit()
        db.refresh(permission)

        return permission

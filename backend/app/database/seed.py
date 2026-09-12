"""Database seeding with test data."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.database.schema import (
    User, Agent, UserCalendar, UserPreference, UserLocation, UserBudget
)
from app.utils.security import hash_password


def seed_data():
    """Seed database with test data for User A and User B."""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("⏭️  Database already seeded, skipping...")
            return

        # ===== USER A (ALICE) =====
        user_a = User(
            username="alice",
            email="alice@example.com",
            hashed_password=hash_password("password123"),
            full_name="Alice Johnson"
        )
        db.add(user_a)
        db.flush()  # Get the user_id

        # Agent A
        agent_a = Agent(
            user_id=user_a.id,
            name="Agent A",
            unique_key="agent_a",
            system_instructions="""You are Agent A, representing Alice Johnson.
            Your purpose is to help coordinate activities on behalf of Alice.
            You can only access Alice's data through proper permission channels.
            Always respect privacy and only request necessary information."""
        )
        db.add(agent_a)

        # User A's Calendar
        now = datetime.utcnow()
        cal_a1 = UserCalendar(
            user_id=user_a.id,
            event_id="evt_a_001",
            event_name="Team Meeting",
            description="Weekly team sync",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
            location="Conference Room A",
            attendees="team@company.com",
            is_free=False
        )
        cal_a2 = UserCalendar(
            user_id=user_a.id,
            event_id="evt_a_002",
            event_name="Lunch",
            description="Lunch break",
            start_time=now + timedelta(hours=5),
            end_time=now + timedelta(hours=6),
            location="Cafeteria",
            is_free=False
        )
        cal_a3 = UserCalendar(
            user_id=user_a.id,
            event_id="evt_a_003",
            event_name="Free Time",
            start_time=now + timedelta(hours=7),
            end_time=now + timedelta(hours=9),
            is_free=True
        )
        db.add_all([cal_a1, cal_a2, cal_a3])

        # User A's Preferences
        pref_a1 = UserPreference(
            user_id=user_a.id,
            preference_key="movie_genre",
            preference_value="action,sci-fi,thriller"
        )
        pref_a2 = UserPreference(
            user_id=user_a.id,
            preference_key="cuisine",
            preference_value="Italian,Thai,Indian"
        )
        db.add_all([pref_a1, pref_a2])

        # User A's Location
        loc_a = UserLocation(
            user_id=user_a.id,
            latitude=40.7128,
            longitude=-74.0060,
            location_name="Office",
            is_home=False
        )
        db.add(loc_a)

        # User A's Budget
        budget_a = UserBudget(
            user_id=user_a.id,
            category="entertainment",
            amount=1000.00,
            currency="INR"
        )
        db.add(budget_a)

        # ===== USER B (BOB) =====
        user_b = User(
            username="bob",
            email="bob@example.com",
            hashed_password=hash_password("password123"),
            full_name="Bob Smith"
        )
        db.add(user_b)
        db.flush()  # Get the user_id

        # Agent B
        agent_b = Agent(
            user_id=user_b.id,
            name="Agent B",
            unique_key="agent_b",
            system_instructions="""You are Agent B, representing Bob Smith.
            Your purpose is to help coordinate activities on behalf of Bob.
            You can only access Bob's data through proper permission channels.
            Always respect privacy and only request necessary information."""
        )
        db.add(agent_b)

        # User B's Calendar
        cal_b1 = UserCalendar(
            user_id=user_b.id,
            event_id="evt_b_001",
            event_name="Project Deadline",
            description="Final project submission",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=4),
            location="Home",
            is_free=False
        )
        cal_b2 = UserCalendar(
            user_id=user_b.id,
            event_id="evt_b_002",
            event_name="Free Evening",
            start_time=now + timedelta(hours=7),
            end_time=now + timedelta(hours=11),
            is_free=True
        )
        db.add_all([cal_b1, cal_b2])

        # User B's Preferences
        pref_b1 = UserPreference(
            user_id=user_b.id,
            preference_key="movie_genre",
            preference_value="action,comedy,drama"
        )
        pref_b2 = UserPreference(
            user_id=user_b.id,
            preference_key="cuisine",
            preference_value="Chinese,Mexican,Indian"
        )
        db.add_all([pref_b1, pref_b2])

        # User B's Location
        loc_b = UserLocation(
            user_id=user_b.id,
            latitude=40.7580,
            longitude=-73.9855,
            location_name="Home",
            is_home=True
        )
        db.add(loc_b)

        # User B's Budget
        budget_b = UserBudget(
            user_id=user_b.id,
            category="entertainment",
            amount=800.00,
            currency="INR"
        )
        db.add(budget_b)

        # Commit all data
        db.commit()
        print("✅ Database seeded with test data")
        print(f"   User A: alice (ID={user_a.id}) with Agent A (ID={agent_a.id})")
        print(f"   User B: bob (ID={user_b.id}) with Agent B (ID={agent_b.id})")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()

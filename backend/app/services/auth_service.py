"""Authentication service."""
from sqlalchemy.orm import Session
from app.database.schema import User
from app.utils.security import hash_password, verify_password, create_access_token
from app.models.user import UserRegisterRequest, UserLoginRequest, TokenResponse


class AuthService:
    """Authentication service."""

    @staticmethod
    def register_user(db: Session, user_data: UserRegisterRequest) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.username == user_data.username
        ).first()
        if existing_user:
            raise ValueError("Username already exists")

        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()
        if existing_email:
            raise ValueError("Email already exists")

        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def login_user(db: Session, user_data: UserLoginRequest) -> TokenResponse:
        """Login a user and return access token."""
        user = db.query(User).filter(
            User.username == user_data.username
        ).first()

        if not user or not verify_password(user_data.password, user.hashed_password):
            raise ValueError("Invalid username or password")

        # Create access token
        access_token = create_access_token(data={"sub": user.username, "user_id": user.id})

        return TokenResponse(
            access_token=access_token,
            user_id=user.id,
            username=user.username
        )

    @staticmethod
    def get_user_by_token(db: Session, user_id: int) -> User:
        """Get user by ID from token."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        return user

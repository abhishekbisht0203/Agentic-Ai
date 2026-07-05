"""
OAuth service handling Google and GitHub authentication flows.

Manages OAuth state verification, token exchange, user info retrieval,
and user creation/linking for OAuth providers.
"""

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security.auth import create_access_token, create_refresh_token
from app.models.user import User, UserSession
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)

STATE_EXPIRY_MINUTES = 10


class OAuthService:
    """Service for OAuth authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    @staticmethod
    def generate_state(provider: str) -> str:
        """Generate a cryptographically secure state token for CSRF protection.

        Args:
            provider: The OAuth provider name (google, github).

        Returns:
            State token hash.
        """
        state_data = secrets.token_urlsafe(32)
        state_hash = hashlib.sha256(state_data.encode()).hexdigest()

        state_payload = {
            "provider": provider,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "used": False,
        }

        try:
            from app.cache.redis.cache import RedisCache
            if RedisCache.is_connected:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(
                    RedisCache.set(
                        f"oauth_state:{state_hash}",
                        json.dumps(state_payload),
                        ex=STATE_EXPIRY_MINUTES * 60,
                    )
                )
                return state_hash
        except Exception:
            pass

        # Fallback: store in database (for single-worker setups)
        _oauth_states_local[state_hash] = state_payload
        return state_hash

    @staticmethod
    async def verify_state(state: str) -> str:
        """Verify and consume an OAuth state token.

        Args:
            state: The state token to verify.

        Returns:
            The provider name associated with the state.

        Raises:
            AuthenticationError: If state is invalid, expired, or already used.
        """
        state_data = None

        # Try Redis first
        try:
            from app.cache.redis.cache import RedisCache
            if RedisCache.is_connected:
                raw = await RedisCache.get(f"oauth_state:{state}")
                if raw:
                    state_data = json.loads(raw)
                    await RedisCache.delete(f"oauth_state:{state}")
        except Exception:
            pass

        # Fallback to local storage
        if state_data is None and state in _oauth_states_local:
            state_data = _oauth_states_local.pop(state)

        if state_data is None:
            raise AuthenticationError(message="Invalid OAuth state")

        if state_data["used"]:
            raise AuthenticationError(message="OAuth state already used")

        created_at = datetime.fromisoformat(state_data["created_at"])
        if datetime.now(timezone.utc) - created_at > timedelta(minutes=STATE_EXPIRY_MINUTES):
            raise AuthenticationError(message="OAuth state expired")

        return state_data["provider"]


# Fallback local storage for single-worker setups
_oauth_states_local: dict[str, dict] = {}

    @staticmethod
    def get_google_auth_url(state: str) -> str:
        """Generate Google OAuth authorization URL.

        Args:
            state: The state token for CSRF protection.

        Returns:
            Full Google OAuth authorization URL.
        """
        params = {
            "client_id": settings.oauth.google_client_id,
            "redirect_uri": settings.oauth.get_google_redirect_uri(),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

    @staticmethod
    def get_github_auth_url(state: str) -> str:
        """Generate GitHub OAuth authorization URL.

        Args:
            state: The state token for CSRF protection.

        Returns:
            Full GitHub OAuth authorization URL.
        """
        params = {
            "client_id": settings.oauth.github_client_id,
            "redirect_uri": settings.oauth.get_github_redirect_uri(),
            "scope": "read:user user:email",
            "state": state,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://github.com/login/oauth/authorize?{query_string}"

    async def exchange_google_code(self, code: str) -> dict:
        """Exchange Google authorization code for tokens and get user info.

        Args:
            code: The authorization code from Google.

        Returns:
            Dictionary with user info (email, name, avatar, google_id).

        Raises:
            AuthenticationError: If token exchange or user info fetch fails.
        """
        async with httpx.AsyncClient() as client:
            # Exchange code for tokens
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.oauth.google_client_id,
                    "client_secret": settings.oauth.google_client_secret,
                    "redirect_uri": settings.oauth.get_google_redirect_uri(),
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                logger.error("Google token exchange failed: %s", token_response.text)
                raise AuthenticationError(message="Failed to exchange Google authorization code")

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise AuthenticationError(message="No access token received from Google")

            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if user_response.status_code != 200:
                logger.error("Google user info fetch failed: %s", user_response.text)
                raise AuthenticationError(message="Failed to fetch user info from Google")

            user_info = user_response.json()

            return {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "avatar_url": user_info.get("picture"),
                "google_id": user_info.get("id"),
                "verified_email": user_info.get("verified_email", False),
            }

    async def exchange_github_code(self, code: str) -> dict:
        """Exchange GitHub authorization code for tokens and get user info.

        Args:
            code: The authorization code from GitHub.

        Returns:
            Dictionary with user info (email, name, avatar, github_id).

        Raises:
            AuthenticationError: If token exchange or user info fetch fails.
        """
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": settings.oauth.github_client_id,
                    "client_secret": settings.oauth.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.oauth.get_github_redirect_uri(),
                },
                headers={"Accept": "application/json"},
            )

            if token_response.status_code != 200:
                logger.error("GitHub token exchange failed: %s", token_response.text)
                raise AuthenticationError(message="Failed to exchange GitHub authorization code")

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise AuthenticationError(message="No access token received from GitHub")

            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            if user_response.status_code != 200:
                logger.error("GitHub user info fetch failed: %s", user_response.text)
                raise AuthenticationError(message="Failed to fetch user info from GitHub")

            user_info = user_response.json()

            # Get user emails
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

            primary_email = None
            if emails_response.status_code == 200:
                emails = emails_response.json()
                for email_data in emails:
                    if email_data.get("primary"):
                        primary_email = email_data.get("email")
                        break
                if not primary_email and emails:
                    primary_email = emails[0].get("email")

            return {
                "email": primary_email or user_info.get("email"),
                "name": user_info.get("name") or user_info.get("login"),
                "avatar_url": user_info.get("avatar_url"),
                "github_id": str(user_info.get("id")),
                "verified_email": primary_email is not None,
            }

    async def authenticate_oauth_user(
        self, user_info: dict, provider: str
    ) -> TokenResponse:
        """Authenticate or create user from OAuth provider info.

        Handles:
        1. Existing user by provider ID (return existing)
        2. Existing user by email (link provider)
        3. New user (create account)

        Args:
            user_info: User information from OAuth provider.
            provider: The OAuth provider name (google, github).

        Returns:
            TokenResponse with JWT tokens.

        Raises:
            AuthenticationError: If authentication fails.
        """
        provider_id_field = f"{provider}_id"
        provider_id = user_info.get(provider_id_field)

        if not provider_id:
            raise AuthenticationError(
                message=f"No {provider} ID received from OAuth provider"
            )

        # Check if user exists with this provider ID
        existing_user = await self.user_repo.get_by_oauth(provider, provider_id)

        if existing_user:
            # Update last login and avatar if needed
            await self.user_repo.update_last_login(existing_user.id)
            if user_info.get("avatar_url") and not existing_user.avatar_url:
                await self.user_repo.update(
                    existing_user.id, avatar_url=user_info["avatar_url"]
                )
            return await self._create_tokens(existing_user)

        # Check if user exists with the same email
        email = user_info.get("email")
        if email:
            existing_email_user = await self.user_repo.get_by_email(email)

            if existing_email_user:
                # Link the OAuth provider to existing account
                update_data = {
                    provider_id_field: provider_id,
                    "oauth_provider": provider,
                    "is_verified": existing_email_user.is_verified or user_info.get("verified_email", False),
                }
                if user_info.get("avatar_url") and not existing_email_user.avatar_url:
                    update_data["avatar_url"] = user_info["avatar_url"]

                await self.user_repo.update(existing_email_user.id, **update_data)
                await self.user_repo.update_last_login(existing_email_user.id)

                return await self._create_tokens(existing_email_user)

        # Create new user
        username = self._generate_username(email, provider, provider_id)

        new_user = await self.user_repo.create_user(
            email=email,
            username=username,
            full_name=user_info.get("name"),
            avatar_url=user_info.get("avatar_url"),
            oauth_provider=provider,
            **{provider_id_field: provider_id},
            is_verified=user_info.get("verified_email", False),
            is_active=True,
        )

        await self.user_repo.update_last_login(new_user.id)
        return await self._create_tokens(new_user)

    @staticmethod
    def _generate_username(email: str, provider: str, provider_id: str) -> str:
        """Generate a unique username for OAuth users.

        Args:
            email: User's email address.
            provider: OAuth provider name.
            provider_id: User's ID from the OAuth provider.

        Returns:
            A unique username string.
        """
        if email:
            base_username = email.split("@")[0]
        else:
            base_username = f"{provider}_{provider_id[:8]}"

        # Clean the username
        base_username = "".join(
            c for c in base_username if c.isalnum() or c in "-_"
        ).lower()

        if len(base_username) < 3:
            base_username = f"{provider}_{base_username}"

        if len(base_username) > 30:
            base_username = base_username[:30]

        return base_username

    async def _create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user.

        Args:
            user: The authenticated user instance.

        Returns:
            TokenResponse with tokens and expiration metadata.
        """
        access_token = create_access_token(
            subject=str(user.id),
            scopes=[user.role.value] if hasattr(user.role, "value") else [str(user.role)],
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.jwt.expiration_hours),
        )
        self.db.add(session)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt.expiration_hours * 3600,
        )

import logging
from fastapi import Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.db.session import get_db
from app.core.config import settings
from app.controller.user_controller import get_user_data
from app.controller.customeruser_controller import get_customeruser_data

# Public routes that skip auth
PUBLIC_ROUTES = ["/", "/auth/customer/login", "/auth/token", "/public-resource", "/docs", "/openapi.json"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def create_error_response(status_code: int, detail: str):
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in PUBLIC_ROUTES:
            return await call_next(request)

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            logger.error("Authorization header missing")
            return create_error_response(401, "Authorization header missing")

        if not authorization.startswith("Bearer "):
            logger.error("Invalid Authorization header format")
            return create_error_response(401, "Invalid Authorization header format")

        token = authorization.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            # FIX: key is "user_type" (with underscore), matching what auth.py encodes
            user_type: str = payload.get("user_type", "agent")

            if not username:
                logger.error("Token missing 'sub' claim")
                return create_error_response(401, "Invalid token")

            db: Session = next(get_db())

            if user_type == "agent":
                user = get_user_data(db, username)
            elif user_type == "customer":
                user = get_customeruser_data(db, username)
            else:
                logger.error(f"Unknown user_type in token: {user_type}")
                return create_error_response(401, "Invalid user_type in token")

            if not user:
                logger.error(f"User '{username}' not found in database")
                return create_error_response(401, "User not found")

            request.state.user = user
            request.state.user_type = user_type

        except JWTError as e:
            logger.error(f"JWT error: {e}")
            return create_error_response(401, "Invalid or expired token")
        except Exception as e:
            logger.error(f"Unhandled auth error: {e}")
            return create_error_response(500, "Internal server error during authentication")

        return await call_next(request)

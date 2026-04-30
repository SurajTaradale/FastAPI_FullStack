from fastapi import FastAPI, Depends
from app.api.v1.user import router as user_router
from app.api.v1.customeruser import router as customeruser_router
from app.api.v1.auth import router as auth_router
from app.api.v1.system import router as system_router
from app.middleware.auth_middleware import AuthMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Initialize FastAPI app
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS — origins come from config/env, not hardcoded
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom JWT authentication middleware
app.add_middleware(AuthMiddleware)


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Helpdesk System"}


# Protected routes (require valid JWT)
app.include_router(user_router, prefix="/api/v1/agent", dependencies=[Depends(oauth2_scheme)])
app.include_router(customeruser_router, prefix="/api/v1/agent", dependencies=[Depends(oauth2_scheme)])
app.include_router(system_router, prefix="/api/v1", dependencies=[Depends(oauth2_scheme)])

# Public + protected auth routes
app.include_router(auth_router, prefix="/auth")

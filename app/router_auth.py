from fastapi import APIRouter, Depends
from services.auth_service import AuthService
from schemas.schemas import (
TokenResponse,
ResponseClient,
ClientCreate,
RefreshResponse,
RefreshRequest,
ChangePassword
)
from fastapi.security import OAuth2PasswordRequestForm
from utils.dependencies import get_current_client


router_auth = APIRouter(prefix="/auth")


@router_auth.post("/register", response_model=ResponseClient)
async def register_client(data: ClientCreate):
    result = await AuthService.register_client(data)
    return result

@router_auth.post("/client_login", response_model=TokenResponse)
async def client_login(data: OAuth2PasswordRequestForm = Depends()):
    result = await AuthService.client_login(data)
    return result

@router_auth.post("/auth/refresh", response_model=RefreshResponse)
async def refresh_token(data: RefreshRequest):
    result = AuthService.refresh_token(data.refresh_token)
    return result

@router_auth.post("/change_password")
async def change_password(data: ChangePassword, current_client=Depends(get_current_client)):
    result = await AuthService.change_password(data, current_client)
    return result
    
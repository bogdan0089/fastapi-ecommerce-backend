from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth_schema import ChangePassword, RefreshRequest, RefreshResponse, TokenResponse
from schemas.client_schema import ClientCreate, ResponseClient
from services.auth_service import AuthService
from utils.dependencies import CurrentClient


router_auth = APIRouter(prefix="/auth")


@router_auth.post("/register", response_model=ResponseClient)
async def register_client(data: ClientCreate) -> ResponseClient:
    return await AuthService.register_client(data)

@router_auth.post("/client_login", response_model=TokenResponse)
async def client_login(data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    return await AuthService.client_login(data)

@router_auth.post("/refresh", response_model=RefreshResponse)
async def refresh_token(data: RefreshRequest) -> RefreshResponse:
    access_token = AuthService.refresh_token(data.refresh_token)
    return RefreshResponse(access_token=access_token)

@router_auth.post("/change_password")
async def change_password(data: ChangePassword, current_client: CurrentClient) -> dict:
    return await AuthService.change_password(data, current_client)

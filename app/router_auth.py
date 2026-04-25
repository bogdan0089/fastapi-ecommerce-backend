from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth_schema import(
ChangePassword,
RefreshRequest,
RefreshResponse,
TokenResponse,
ChangeRole,
ResetPassword,
ForgotPassword
)
from schemas.client_schema import ClientCreate, ResponseClient
from services.auth_service import AuthService
from utils.dependencies import CurrentClient, CurrentAdmin, RateLimit


router_auth = APIRouter(prefix="/auth")


@router_auth.post("/register")
async def register_client(data: ClientCreate, _: RateLimit):
    return await AuthService.register_client(data)

@router_auth.post("/client_login", response_model=TokenResponse)
async def client_login(_: RateLimit, data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    return await AuthService.client_login(data)

@router_auth.post("/refresh", response_model=RefreshResponse)
async def refresh_token(data: RefreshRequest) -> RefreshResponse:
    access_token = AuthService.refresh_token(data.refresh_token)
    return RefreshResponse(access_token=access_token)

@router_auth.post("/change_password")
async def change_password(data: ChangePassword, current_client: CurrentClient) -> dict:
    return await AuthService.change_password(data, current_client)

@router_auth.post("/change_role/{client_id}", response_model=ResponseClient)
async def change_role(client_id: int, data: ChangeRole, _: CurrentAdmin):
    return await AuthService.change_role(client_id, data)

@router_auth.get("/verify/{token}")
async def verify_email(token: str):
    return await AuthService.verify_email(token)

@router_auth.post("/forgot_password")
async def forgot_password(data: ForgotPassword, _: RateLimit):
    return await AuthService.forgot_password(data)

@router_auth.post("/reset_password")
async def reset_password(data: ResetPassword):
    return await AuthService.reset_password(data)
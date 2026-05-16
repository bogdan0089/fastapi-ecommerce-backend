from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth.input_dto import (
    ChangePasswordDTO,
    RefreshRequestDTO,
    ChangeRoleDTO,
    ResetPasswordDTO,
    ForgotPasswordDTO,
)
from schemas.auth.output_dto import TokenOutputDTO, RefreshOutputDTO
from schemas.client.input_dto import ClientCreateDTO
from schemas.client.output_dto import ClientOutputDTO
from services.auth_service import AuthService
from utils.dependencies import CurrentClient, CurrentAdmin, RateLimit


router_auth = APIRouter(prefix="/auth", tags=["Auth"])


@router_auth.post("/register")
async def register_client(data: ClientCreateDTO, _: RateLimit):
    return await AuthService.register_client(data)

@router_auth.post("/client_login", response_model=TokenOutputDTO)
async def client_login(_: RateLimit, data: OAuth2PasswordRequestForm = Depends()) -> TokenOutputDTO:
    return await AuthService.client_login(data)

@router_auth.post("/refresh", response_model=RefreshOutputDTO)
async def refresh_token(data: RefreshRequestDTO) -> RefreshOutputDTO:
    access_token = AuthService.refresh_token(data.refresh_token)
    return RefreshOutputDTO(access_token=access_token)

@router_auth.post("/change_password")
async def change_password(data: ChangePasswordDTO, current_client: CurrentClient) -> dict:
    return await AuthService.change_password(data, current_client)

@router_auth.post("/change_role/{client_id}", response_model=ClientOutputDTO)
async def change_role(client_id: int, data: ChangeRoleDTO, _: CurrentAdmin):
    return await AuthService.change_role(client_id, data)

@router_auth.get("/verify/{token}")
async def verify_email(token: str):
    return await AuthService.verify_email(token)

@router_auth.post("/forgot_password")
async def forgot_password(data: ForgotPasswordDTO, _: RateLimit):
    return await AuthService.forgot_password(data)

@router_auth.post("/reset_password")
async def reset_password(data: ResetPasswordDTO):
    return await AuthService.reset_password(data)

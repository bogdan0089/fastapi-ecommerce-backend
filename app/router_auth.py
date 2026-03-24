from fastapi import APIRouter, Depends
from services.auth_service import AuthService
from schemas.schemas import TokenResponse, ResponseClient, ClientCreate
from fastapi.security import OAuth2PasswordRequestForm


router_auth = APIRouter(prefix="/auth")


@router_auth.post("/register", response_model=ResponseClient)
async def register_client(data: ClientCreate):
    return await AuthService.register_client(data)

@router_auth.post("/client_login", response_model=TokenResponse)
async def client_login(data: OAuth2PasswordRequestForm = Depends()):
    return await AuthService.client_login(data)
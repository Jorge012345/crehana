"""Authentication router."""

from fastapi import APIRouter, Depends

from src.application.auth_service import AuthService
from src.application.dto import LoginDTO, TokenResponseDTO, UserCreateDTO, UserResponseDTO
from src.presentation.dependencies import get_auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponseDTO)
async def register(
    user_data: UserCreateDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    login_data: LoginDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login user and get access token."""
    return await auth_service.authenticate_user(login_data) 
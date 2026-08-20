from fastapi import APIRouter
from .endpoints import steam


v1_router = APIRouter()
v1_router.include_router(steam.router)

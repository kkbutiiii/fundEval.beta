"""Routers module."""
from .funds import router as funds_router
from .portfolios import router as portfolios_router
from .auth import router as auth_router
from .watchlists import router as watchlists_router

__all__ = ["funds_router", "portfolios_router", "auth_router", "watchlists_router"]

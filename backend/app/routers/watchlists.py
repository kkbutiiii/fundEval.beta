"""
Watchlist API router.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models.watchlist import WatchlistDB
from app.db_models.user import UserDB
from app.models.watchlist import WatchlistFundCreate, WatchlistListResponse, WatchlistFundResponse
from app.routers.auth import get_current_active_user

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=WatchlistListResponse)
async def get_watchlist(
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's watchlist."""
    result = await db.execute(
        select(WatchlistDB)
        .where(WatchlistDB.user_id == current_user.id)
        .order_by(WatchlistDB.added_at.desc())
    )
    watchlist = result.scalars().all()

    return WatchlistListResponse(
        watchlist=[WatchlistFundResponse.model_validate(item) for item in watchlist],
        total=len(watchlist)
    )


@router.post("", response_model=WatchlistFundResponse, status_code=201)
async def add_to_watchlist(
    data: WatchlistFundCreate,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a fund to watchlist.

    - **fund_code**: Fund code
    - **fund_name**: Fund name
    """
    # Check if already in watchlist
    result = await db.execute(
        select(WatchlistDB).where(
            WatchlistDB.user_id == current_user.id,
            WatchlistDB.fund_code == data.fund_code
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Return existing entry
        return WatchlistFundResponse.model_validate(existing)

    # Create new watchlist entry
    watchlist_item = WatchlistDB(
        user_id=current_user.id,
        fund_code=data.fund_code,
        fund_name=data.fund_name
    )

    db.add(watchlist_item)
    await db.commit()
    await db.refresh(watchlist_item)

    return WatchlistFundResponse.model_validate(watchlist_item)


@router.delete("/{fund_code}", status_code=204)
async def remove_from_watchlist(
    fund_code: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a fund from watchlist."""
    result = await db.execute(
        delete(WatchlistDB).where(
            WatchlistDB.user_id == current_user.id,
            WatchlistDB.fund_code == fund_code
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found in watchlist"
        )

    await db.commit()
    return None


@router.get("/{fund_code}", response_model=WatchlistFundResponse)
async def check_watchlist(
    fund_code: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if a fund is in watchlist."""
    result = await db.execute(
        select(WatchlistDB).where(
            WatchlistDB.user_id == current_user.id,
            WatchlistDB.fund_code == fund_code
        )
    )
    watchlist_item = result.scalar_one_or_none()

    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found in watchlist"
        )

    return WatchlistFundResponse.model_validate(watchlist_item)

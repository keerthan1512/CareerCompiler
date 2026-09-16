"""
Auth router — Phase 1 dev bypass.
In Phase 7 this is replaced with Firebase Auth token verification.

Dev bypass: Pass X-Dev-User-Id header to identify the user.
A dev user record is auto-created on first use.
"""

from __future__ import annotations

import uuid
import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_current_user(
    x_dev_user_id: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: resolve the current user.

    Phase 1 (DEV_AUTH_BYPASS=true):
        Reads X-Dev-User-Id header and auto-creates user if needed.

    Phase 7+:
        Verify Firebase JWT token and look up user by firebase_uid.
    """
    if not settings.dev_auth_bypass:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Production auth not yet implemented. Set DEV_AUTH_BYPASS=true for development.",
        )

    # Use the header value or fall back to the configured dev user ID
    user_id_str = x_dev_user_id or settings.dev_user_id

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-Dev-User-Id: must be a valid UUID. Got: {user_id_str}",
        )

    # Look up user
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Auto-create dev user if not exists
    if user is None:
        logger.info("Auto-creating dev user %s", user_uuid)
        user = User(
            id=user_uuid,
            email=f"dev-{user_uuid}@careercompiler.local",
            name="Dev User",
            role="individual",
        )
        db.add(user)
        await db.flush()

    return user

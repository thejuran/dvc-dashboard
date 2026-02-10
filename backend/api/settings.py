from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.models.app_setting import AppSetting
from backend.api.schemas import AppSettingResponse, AppSettingUpdate

router = APIRouter(tags=["settings"])

# Valid settings keys and their allowed values
SETTINGS_SCHEMA = {
    "borrowing_limit_pct": {"allowed": ["50", "100"], "default": "100"},
}


@router.get("/api/settings", response_model=list[AppSettingResponse])
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """Return all app settings as a list."""
    result = await db.execute(select(AppSetting))
    return result.scalars().all()


@router.get("/api/settings/{key}", response_model=AppSettingResponse)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Get a single setting by key."""
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return setting


@router.put("/api/settings/{key}", response_model=AppSettingResponse)
async def update_setting(key: str, data: AppSettingUpdate, db: AsyncSession = Depends(get_db)):
    """Update a setting value. Only known keys with valid values are accepted."""
    if key not in SETTINGS_SCHEMA:
        raise HTTPException(status_code=404, detail=f"Unknown setting '{key}'")

    schema = SETTINGS_SCHEMA[key]
    if data.value not in schema["allowed"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid value '{data.value}' for '{key}'. Allowed: {schema['allowed']}"
        )

    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        # Auto-create if migration seed was missed
        setting = AppSetting(key=key, value=data.value)
        db.add(setting)
    else:
        setting.value = data.value

    await db.commit()
    await db.refresh(setting)
    return setting

"""Seed required single-user and native-source defaults idempotently."""

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Source, User, UserSetting
from app.prompting import sync_builtin_prompts
from app.security import hash_password


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not user:
            user = User(
                email=settings.admin_email.lower(),
                password_hash=hash_password(settings.admin_password),
            )
            db.add(user)
            db.flush()
        if not db.get(UserSetting, user.id):
            db.add(UserSetting(user_id=user.id))
        if not db.scalar(select(Source).where(Source.is_native.is_(True))):
            db.add(
                Source(
                    name="StarMem Native",
                    source_type="native",
                    description="Content captured directly in StarMem.",
                    is_native=True,
                )
            )
        sync_builtin_prompts(db)
        db.commit()


if __name__ == "__main__":
    main()

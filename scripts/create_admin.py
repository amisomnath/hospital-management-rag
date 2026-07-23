"""Create or promote an administrative user from the command line."""

import argparse
import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.security import hash_password
from app.crud.user import get_user_by_email
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User


def main() -> None:
    """Create an admin without exposing its password in shell history."""

    parser = argparse.ArgumentParser(description="Create or promote an admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Admin password (minimum 8 characters): ")

    if get_settings().database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = get_user_by_email(db, args.email.lower())
        if user is None:
            user = User(
                email=args.email.lower(),
                full_name=args.name,
                hashed_password=hash_password(password),
                role="admin",
                is_active=True,
            )
            db.add(user)
            action = "Created"
        else:
            user.full_name = args.name
            user.hashed_password = hash_password(password)
            user.role = "admin"
            user.is_active = True
            action = "Updated"
        db.commit()
        print(f"{action} admin user {user.email}.")


if __name__ == "__main__":
    main()

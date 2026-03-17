"""
Initialize admin user script.
Creates the default admin account if it doesn't exist.

Usage:
    cd backend
    python -m scripts.init_admin
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, init_db
from app.db_models.user import UserDB
from app.utils.security import get_password_hash


# Default admin credentials
ADMIN_USERNAME = "fevadmin"
ADMIN_PASSWORD = "feva3316"


async def create_admin_user(db: AsyncSession) -> UserDB:
    """Create admin user if it doesn't exist."""
    # Check if admin already exists
    result = await db.execute(
        select(UserDB).where(UserDB.username == ADMIN_USERNAME)
    )
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        print(f"Admin user '{ADMIN_USERNAME}' already exists.")
        print(f"  - ID: {existing_admin.id}")
        print(f"  - Is Admin: {existing_admin.is_admin}")
        print(f"  - Is Active: {existing_admin.is_active}")
        print(f"  - Created At: {existing_admin.created_at}")
        return existing_admin

    # Create new admin user
    admin_user = UserDB(
        username=ADMIN_USERNAME,
        password_hash=get_password_hash(ADMIN_PASSWORD),
        is_admin=True,
        is_active=True
    )

    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    print(f"Admin user '{ADMIN_USERNAME}' created successfully!")
    print(f"  - ID: {admin_user.id}")
    print(f"  - Username: {admin_user.username}")
    print(f"  - Is Admin: {admin_user.is_admin}")
    print(f"  - Is Active: {admin_user.is_active}")

    return admin_user


async def main():
    """Main function."""
    print("Initializing admin user...")
    print("=" * 50)

    # Initialize database tables
    print("\n1. Initializing database...")
    await init_db()
    print("   Database initialized.")

    # Create admin user
    print(f"\n2. Creating admin user '{ADMIN_USERNAME}'...")
    async with AsyncSessionLocal() as db:
        admin = await create_admin_user(db)

    print("\n" + "=" * 50)
    print("Admin initialization complete!")
    print(f"\nYou can now login with:")
    print(f"  Username: {ADMIN_USERNAME}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print("\nIMPORTANT: Please change the default password after first login!")


if __name__ == "__main__":
    asyncio.run(main())

"""
Database seeder - Creates default admin user
"""
import asyncio
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.shared.models import User, Organization
from app.core.security import get_password_hash


async def seed_database():
    """Seed database with default admin user"""

    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        result = await db.execute(
            select(User).where(User.email == "admin@admin.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("✓ Admin user already exists")
            print(f"  Email: admin@admin.com")
            return

        # Check if default organization exists
        result = await db.execute(
            select(Organization).where(Organization.slug == "default-org")
        )
        organization = result.scalar_one_or_none()

        if not organization:
            # Create default organization
            organization = Organization(
                name="Default Organization",
                slug="default-org",
                is_active=True
            )
            db.add(organization)
            await db.flush()
            print("✓ Created default organization")

        # Create admin user
        admin_user = User(
            email="admin@admin.com",
            hashed_password=get_password_hash("admin"),
            full_name="Administrator",
            role="admin",
            is_active=True,
            is_verified=True,
            organization_id=organization.id
        )

        db.add(admin_user)
        await db.commit()

        print("=" * 50)
        print("✅ Database seeded successfully!")
        print("=" * 50)
        print("")
        print("Default Admin Credentials:")
        print("  Email:    admin@admin.com")
        print("  Password: admin")
        print("")
        print("⚠️  IMPORTANT: Change this password in production!")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_database())

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.site import Site
from app.core.security import get_password_hash


async def seed_database():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Create default organization
            result = await session.execute(
                select(Organization).where(Organization.name == "Default Organization")
            )
            org = result.scalar_one_or_none()

            if not org:
                org = Organization(
                    name="Default Organization",
                    description="Default organization for development"
                )
                session.add(org)
                await session.commit()
                await session.refresh(org)
                print(f"Created organization: {org.name}")
            else:
                print("Organization already exists")

            # Create admin user
            result = await session.execute(
                select(User).where(User.email == "admin@admin.com")
            )
            admin = result.scalar_one_or_none()

            if not admin:
                admin = User(
                    email="admin@admin.com",
                    full_name="Admin User",
                    hashed_password=get_password_hash("admin"),
                    role="admin",
                    organization_id=org.id,
                    is_active=True
                )
                session.add(admin)
                await session.commit()
                await session.refresh(admin)
                print(f"Created admin user: {admin.email}")
            else:
                print("Admin user already exists")

            # Create sample site
            result = await session.execute(
                select(Site).where(Site.name == "Google")
            )
            site = result.scalar_one_or_none()

            if not site:
                site = Site(
                    name="Google",
                    url="https://google.com",
                    description="Sample site for testing",
                    is_active=True,
                    organization_id=org.id
                )
                session.add(site)
                await session.commit()
                await session.refresh(site)
                print(f"Created sample site: {site.name}")
            else:
                print("Sample site already exists")

            print("\n" + "="*50)
            print("Database seeded successfully!")
            print("="*50)
            print("\nLogin credentials:")
            print("  Email:    admin@admin.com")
            print("  Password: admin")
            print()

        except Exception as e:
            print(f"Error seeding database: {e}")
            await session.rollback()
            raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())

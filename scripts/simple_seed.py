"""Simple seed script to create default admin user."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User


def seed_users():
    """Create default admin and sample users."""
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Check if admin already exists
        existing_admin = session.exec(select(User).where(User.email == "admin@kolmanagement.com")).first()
        if existing_admin:
            print("Admin user already exists. Skipping seed.")
            return
        
        # Create admin user
        admin = User(
            email="admin@kolmanagement.com",
            hashed_password=hash_password("Admin@123"),
            full_name="System Administrator",
            role="admin",
            is_active=True
        )
        session.add(admin)
        print("✓ Created admin user: admin@kolmanagement.com / Admin@123")
        
        # Create campaign manager
        campaign_manager = User(
            email="manager@kolmanagement.com",
            hashed_password=hash_password("Manager@123"),
            full_name="Campaign Manager",
            role="campaign_manager",
            is_active=True
        )
        session.add(campaign_manager)
        print("✓ Created campaign manager: manager@kolmanagement.com / Manager@123")
        
        # Create account executive
        account_exec = User(
            email="ae@kolmanagement.com",
            hashed_password=hash_password("AccountExec@123"),
            full_name="Account Executive",
            role="account_executive",
            is_active=True
        )
        session.add(account_exec)
        print("✓ Created account executive: ae@kolmanagement.com / AccountExec@123")
        
        # Create viewer
        viewer = User(
            email="viewer@kolmanagement.com",
            hashed_password=hash_password("Viewer@123"),
            full_name="Viewer User",
            role="viewer",
            is_active=True
        )
        session.add(viewer)
        print("✓ Created viewer: viewer@kolmanagement.com / Viewer@123")
        
        session.commit()
        print("\n✅ Database seeded successfully!")
        print("\nDefault users created:")
        print("  Admin: admin@kolmanagement.com / Admin@123")
        print("  Campaign Manager: manager@kolmanagement.com / Manager@123")
        print("  Account Executive: ae@kolmanagement.com / AccountExec@123")
        print("  Viewer: viewer@kolmanagement.com / Viewer@123")


if __name__ == "__main__":
    seed_users()
"""
Quick test script to verify User model works with database
"""
from sqlmodel import Session, select
from app.core.database import engine
from app.models.user import User
from app.models.enums import Role
import bcrypt

def test_create_user():
    """Test creating a user in the database"""
    with Session(engine) as session:
        # Create a test user
        password = "test_password_123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            email="admin@example.com",
            hashed_password=hashed_password,
            full_name="Admin User",
            role="admin",  # Use lowercase string directly
            is_active=True
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        print(f"✅ User created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Role: {user.role}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Created At: {user.created_at}")
        
        return user.id

def test_read_user(user_id: int):
    """Test reading a user from the database"""
    with Session(engine) as session:
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        
        if user:
            print(f"\n✅ User retrieved successfully!")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
        else:
            print(f"\n❌ User not found")

def test_list_users():
    """Test listing all users"""
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        
        print(f"\n✅ Total users in database: {len(users)}")
        for user in users:
            print(f"   - {user.email} ({user.role})")

if __name__ == "__main__":
    print("Testing User Model with PostgreSQL\n")
    print("=" * 50)
    
    try:
        # Test create
        user_id = test_create_user()
        
        # Test read
        test_read_user(user_id)
        
        # Test list
        test_list_users()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

"""Docker startup script."""
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.core.security import hash_password


def wait_for_db():
    """Wait for database to be ready."""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            print("✅ Database is ready!")
            return True
        except Exception as e:
            retry_count += 1
            print(f"⏳ Waiting for database... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    print("❌ Database connection failed after 30 retries")
    return False


def create_simple_user():
    """Create a simple admin user without complex models."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        # Create user table if not exists
        with engine.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'admin',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP
                );
            """)
            
            # Check if admin exists
            result = conn.execute(
                "SELECT COUNT(*) FROM users WHERE email = 'admin@kolmanagement.com'"
            ).fetchone()
            
            if result[0] == 0:
                # Create admin user
                hashed_pw = hash_password("Admin@123")
                conn.execute("""
                    INSERT INTO users (email, hashed_password, full_name, role, is_active)
                    VALUES ('admin@kolmanagement.com', %s, 'System Administrator', 'admin', TRUE)
                """, (hashed_pw,))
                conn.commit()
                print("✅ Created admin user: admin@kolmanagement.com / Admin@123")
            else:
                print("ℹ️ Admin user already exists")
                
    except Exception as e:
        print(f"⚠️ Could not create user: {e}")


if __name__ == "__main__":
    print("🚀 Starting Docker initialization...")
    
    if wait_for_db():
        create_simple_user()
        print("✅ Docker startup completed!")
    else:
        print("❌ Docker startup failed!")
        sys.exit(1)
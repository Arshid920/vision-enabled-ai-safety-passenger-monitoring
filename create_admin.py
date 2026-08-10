from web_app.database import SessionLocal
from web_app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def create_admin():
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("Admin user already exists.")
        return

    hashed_password = pwd_context.hash("admin123")
    new_admin = User(
        username="admin",
        hashed_password=hashed_password,
        role="admin",
        is_active=1
    )
    db.add(new_admin)
    db.commit()
    print("Admin user created: admin / admin123")
    db.close()

if __name__ == "__main__":
    create_admin()

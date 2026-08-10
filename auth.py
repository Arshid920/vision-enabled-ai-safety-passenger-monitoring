from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .. import models, database
from ..database import get_db
from passlib.context import CryptContext
from starlette.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

templates = Jinja2Templates(directory="web_app/templates")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        # In a real app, flash a message here
        return templates.TemplateResponse(request, "auth/login.html", {"error": "Invalid credentials"})
    
    if user.role != role:
         return templates.TemplateResponse(request, "auth/login.html", {"error": "Invalid role for this user"})

    # Simple session management (In production use JWT/SessionMiddleware)
    response = RedirectResponse(url="/transition" if role == "driver" else "/admin", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html")

@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(None),
    username: str = Form(...),
    password: str = Form(...),
    license_number: str = Form(...),
    boat_number: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(models.User).filter(models.User.username == username).first()
    if user:
        return templates.TemplateResponse(request, "auth/register.html", {"error": "Username already taken"})

    hashed_password = get_password_hash(password)
    new_user = models.User(
        username=username,
        hashed_password=hashed_password,
        role="driver",
        full_name=full_name,
        license_number=license_number,
        boat_number=boat_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/auth/login?role=driver", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response

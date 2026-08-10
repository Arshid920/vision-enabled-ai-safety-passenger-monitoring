from fastapi import APIRouter, Depends, Request, Cookie, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, database
from ..database import get_db
from starlette.templating import Jinja2Templates
from datetime import datetime
from ..services import ml_wrapper

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="web_app/templates")


# ── Auth helper ───────────────────────────────────────────────────────────────

def get_current_user(user_id: str, db: Session):
    if not user_id:
        return None
    try:
        return db.query(models.User).filter(models.User.id == int(user_id)).first()
    except (ValueError, TypeError):
        return None


# ── Driver Dashboard ──────────────────────────────────────────────────────────

@router.get("/dashboard")
async def driver_dashboard(request: Request, user_id: str = Cookie(None), active_trip_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "driver":
        return RedirectResponse(url="/auth/login?role=driver", status_code=303)
        
    trip = None
    if active_trip_id:
        trip = db.query(models.Trip).filter(models.Trip.id == int(active_trip_id)).first()
        
    return templates.TemplateResponse(request, "dashboard.html", {"user": user, "trip": trip})

@router.get("/pre_voyage")
async def driver_pre_voyage(request: Request, user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "driver":
        return RedirectResponse(url="/auth/login?role=driver", status_code=303)
    return templates.TemplateResponse(request, "pre_voyage.html", {"user": user})

@router.get("/transition")
async def driver_transition(request: Request, user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "driver":
        return RedirectResponse(url="/auth/login?role=driver", status_code=303)
    return templates.TemplateResponse(request, "transition.html", {"user": user})

@router.get("/api/predict")
async def api_predict(wind: str, wave: str, weather: str, day: str, boat: str):
    prediction = ml_wrapper.predict_safety(wind, wave, weather, day, boat)
    return {"prediction": prediction}

@router.post("/api/log_blocked")
async def log_blocked(user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "driver":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    new_trip = models.Trip(
        driver_id=user.id,
        safety_status="Unsafe",
        alert_count=-1,  # Flag for blocked / not started
        end_time=datetime.utcnow()
    )
    db.add(new_trip)
    db.commit()
    return JSONResponse({"status": "logged"})

@router.post("/voyage/start")
async def voyage_start(
    request: Request,
    wind: str = Form(...),
    wave: str = Form(...),
    weather: str = Form(...),
    day: str = Form(...),
    boat: str = Form(...),
    prediction: str = Form(...),
    user_id: str = Cookie(None),
    db: Session = Depends(get_db)
):
    user = get_current_user(user_id, db)
    if not user or user.role != "driver":
        return RedirectResponse(url="/auth/login?role=driver", status_code=303)
        
    # Create the trip
    new_trip = models.Trip(
        driver_id=user.id,
        safety_status=prediction
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    # For CV service, maybe we need the trip_id. Let's just save it in cookie.
    response.set_cookie(key="active_trip_id", value=str(new_trip.id))
    return response

@router.post("/voyage/end_current")
async def voyage_end_current(user_id: str = Cookie(None), active_trip_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "driver":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    if active_trip_id:
        trip = db.query(models.Trip).filter(models.Trip.id == int(active_trip_id)).first()
        if trip and not trip.end_time:
            trip.end_time = datetime.utcnow()
            db.commit()
            
    response = JSONResponse({"status": "ended"})
    response.delete_cookie("active_trip_id")
    return response


# ── Admin Dashboard ───────────────────────────────────────────────────────────

@router.get("/admin")
async def admin_dashboard(request: Request, user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/auth/login?role=admin", status_code=303)

    drivers = db.query(models.User).filter(models.User.role == "driver").all()
    trips   = (
        db.query(models.Trip)
        .join(models.User, models.Trip.driver_id == models.User.id)
        .order_by(models.Trip.start_time.desc())
        .all()
    )

    valid_trips = [t for t in trips if t.safety_status != "Unsafe"]
    unsafe_trips = [t for t in trips if t.safety_status == "Unsafe"]

    total_voyages  = len(trips)
    active_voyages = sum(1 for t in valid_trips if t.end_time is None)
    unsafe_voyages = len(unsafe_trips)

    return templates.TemplateResponse(request, "admin_dashboard.html", {
        "user": user,
        "drivers": drivers,
        "trips": valid_trips,
        "unsafe_trips": unsafe_trips,
        "total_drivers": len(drivers),
        "total_voyages": total_voyages,
        "active_voyages": active_voyages,
        "unsafe_voyages": unsafe_voyages,
    })


# ── Voyage Detail ─────────────────────────────────────────────────────────────

@router.get("/admin/voyage/{trip_id}")
async def voyage_detail(trip_id: int, request: Request, user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/auth/login?role=admin", status_code=303)

    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        return RedirectResponse(url="/admin", status_code=303)

    logs = db.query(models.SafetyLog).filter(models.SafetyLog.trip_id == trip_id).order_by(models.SafetyLog.timestamp).all()

    duration = None
    if trip.end_time and trip.start_time:
        delta = trip.end_time - trip.start_time
        mins = int(delta.total_seconds() // 60)
        secs = int(delta.total_seconds() % 60)
        duration = f"{mins}m {secs}s"

    return templates.TemplateResponse(request, "voyage_detail.html", {
        "user": user,
        "trip": trip,
        "logs": logs,
        "duration": duration,
    })

@router.post("/admin/voyage/{trip_id}/end")
async def end_voyage(trip_id: int, user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        return JSONResponse({"error": "Trip not found"}, status_code=404)
        
    if not trip.end_time:
        trip.end_time = datetime.utcnow()
        db.commit()
    return JSONResponse({"status": "ended", "trip_id": trip.id})

# ── Driver Toggle (activate / deactivate) ─────────────────────────────────────

@router.post("/admin/driver/{driver_id}/toggle")
async def toggle_driver(driver_id: int, user_id: str = Cookie(None), db: Session = Depends(get_db)):
    user = get_current_user(user_id, db)
    if not user or user.role != "admin":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    driver = db.query(models.User).filter(models.User.id == driver_id, models.User.role == "driver").first()
    if not driver:
        return JSONResponse({"error": "Driver not found"}, status_code=404)

    driver.is_active = 0 if driver.is_active else 1
    db.commit()
    return JSONResponse({"is_active": driver.is_active, "username": driver.username})

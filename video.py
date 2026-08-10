from fastapi import APIRouter, Cookie
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse

from ..services import cv_service
from ..services.safety_predictor import predict_safety, safety_color

router = APIRouter(
    prefix="/video",
    tags=["Video"],
)


@router.get("/feed")
async def video_feed(user_id: str = Cookie(None)):
    """Live MJPEG stream from the boat camera. Requires login."""
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    return StreamingResponse(
        cv_service.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/status")
async def video_status(user_id: str = Cookie(None)):
    """
    JSON snapshot of the current CV analysis.
    Polled every 2 s by the dashboard frontend.
    Returns safety_level and Bootstrap color alongside raw CV fields.
    """
    if not user_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    s = cv_service.get_status()
    level = predict_safety(
        people_count=s["people_count"],
        overcrowded=s["overcrowded"],
        stepped_out=s["stepped_out"],
        life_jacket_ok=s["life_jacket_ok"],
    )
    return JSONResponse({
        "people_count": s.get("people_count", 0),
        "overcrowded": s.get("overcrowded", False),
        "stepped_out": s.get("stepped_out", False),
        "out_of_bounds_count": s.get("out_of_bounds_count", 0),
        "life_jacket_ok": s.get("life_jacket_ok", False),
        "life_jacket_worn": s.get("life_jacket_worn", 0),
        "life_jacket_not_worn": s.get("life_jacket_not_worn", 0),
        "camera_ok": s.get("camera_ok", False),
        "safety_level": level,
        "safety_color": safety_color(level),
    })

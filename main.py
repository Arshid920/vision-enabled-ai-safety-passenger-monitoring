from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import os

from web_app.services import cv_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background camera capture thread on server startup
    cv_service.start()
    yield
    cv_service.stop()

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="web_app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web_app/templates")

from web_app.routers import auth, dashboard, video
from web_app import models, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(video.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("web_app.main:app", host="0.0.0.0", port=port, reload=True)

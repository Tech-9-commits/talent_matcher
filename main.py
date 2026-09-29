import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.v1.search import router as search_router

app = FastAPI(title="Talent Matcher Pro API")

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(search_router, prefix="/api/v1")

# Mount static folder if it exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve UI at the root route "/"
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = os.path.join("static", "index.html")
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Talent Matcher Pro API is Running</h1><p>UI file index.html not found in /static folder.</p>"
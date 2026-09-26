from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.modules.schedule.routes import router as schedule_router

app = FastAPI(title="MediAdhere API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Person 2 Router Registration
app.include_router(schedule_router, prefix="/api/schedule", tags=["Schedule"])

@app.get("/")
def read_root():
    return {"status": "ok", "app": "MediAdhere API"}

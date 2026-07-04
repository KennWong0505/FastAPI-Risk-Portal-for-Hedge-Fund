from fastapi import FastAPI
from routers import risk
from database.db import Base, engine
from fastapi.middleware.cors import CORSMiddleware

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Risk Portal",
    description="Production-grade portfolio risk API for equity and macro strategies.",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def get_health_info():
    """Returns API health status. Used by load balancers and monitoring systems."""
    return {"status": "ok"}

app.include_router(risk.router)
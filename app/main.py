from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, products, employees, stats

app = FastAPI(title="iStock API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://istock-front.netlify.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API iStock opérationnelle 🚀"}

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(employees.router)
app.include_router(stats.router)

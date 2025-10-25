# main.py
from fastapi import FastAPI
import models
from db import engine
from route import customer_router, admin_router
import os

# === ONLY CREATE TABLES IN PRODUCTION ===
if os.getenv("TESTING", "false").lower() != "true":
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Bank", version="1.0")
app.include_router(customer_router)
app.include_router(admin_router)
# main.py
from fastapi import FastAPI
from db import engine
import models
from route import customer_router, admin_router

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Bank", version="1.0")

app.include_router(customer_router)
app.include_router(admin_router)
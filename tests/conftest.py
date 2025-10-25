# tests/conftest.py
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# === FORCE TEST MODE ===
os.environ["TESTING"] = "true"

# === IMPORT MODELS (KYC skipped) ===
import models
from models import Customer, Admin, Account, Transaction

# === IMPORT APP AFTER MODELS (main.py will skip create_all) ===
from main import app
from db import get_db

# === IN-MEMORY SQLITE ===
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# === SAFE TABLES ONLY ===
SAFE_TABLES = [
    Customer.__table__,
    Admin.__table__,
    Account.__table__,
    Transaction.__table__
]

def create_safe_tables():
    # Drop and recreate only safe tables
    for table in SAFE_TABLES:
        table.drop(bind=engine, checkfirst=True)
    for table in SAFE_TABLES:
        table.create(bind=engine, checkfirst=True)

# === CREATE ONCE AT START ===
create_safe_tables()

# === DEPENDENCY OVERRIDE ===
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# === FIXTURES ===
@pytest.fixture(scope="function")
def client():
    # Fresh DB per test
    create_safe_tables()
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
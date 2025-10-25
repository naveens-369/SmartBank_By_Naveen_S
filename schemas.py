# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None  # "customer" or "admin"

# Customer
class Register(BaseModel):
    name: str
    phoneno: int
    age: int
    address: str
    email: EmailStr
    password: str

    class Config:
        orm_mode = True

class Login(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True

class KycUpload(BaseModel):
    aadhar_card: str
    pan_card: str

    class Config:
        orm_mode = True


# Admin
class AdminRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    class Config:
        orm_mode = True

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


# KYC Status Update
class KycStatusUpdate(BaseModel):
    approved: bool


# Accounts
class AccountCreate(BaseModel):
    type: Literal["savings", "current", "fd"]
    nominee_name: str
    initial_deposit: float = 0.0   # optional for FD, required for others

    class Config:
        orm_mode = True

class AccountResponse(BaseModel):
    acc_no: int
    type: str
    balance: float
    nominee_name: str
    created_at: datetime

    class Config:
        orm_mode = True

class TransferRequest(BaseModel):
    from_acc_no: int
    to_acc_no: int
    amount: float

    class Config:
        orm_mode = True

class TransferResponse(BaseModel):
    txn_id: str
    amount: float
    status: str
    timestamp: datetime
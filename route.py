# route.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Header
from sqlalchemy.orm import Session
import schemas, crud, models
from db import get_db

from fastapi import status as http_status

# Routers
customer_router = APIRouter(prefix="/customers", tags=["Customers"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# Customer Routes
@customer_router.post("/register")
def customer_register(user: schemas.Register, db: Session = Depends(get_db)):
    return crud.cust_register(db, user)

@customer_router.post("/login")
def customer_login(login: schemas.Login, db: Session = Depends(get_db)):
    return crud.cust_login(db, login)

@customer_router.post("/upload_kyc")
async def upload_kyc(
    cust_id: int = Form(...),
    aadhar_card: str = Form(...),
    pan_card: str = Form(...),
    kyc_doc: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return crud.upload_kyc(db, cust_id, aadhar_card, pan_card, kyc_doc)


# Admin
def require_admin(
    x_admin_id: int = Header(..., alias="X-Admin-ID"),
    db: Session = Depends(get_db)
):
    admin = db.query(models.Admin).filter(models.Admin.admin_id == x_admin_id).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid or missing Admin ID")
    return admin


# Admin Routes
@admin_router.post("/register")
def admin_register(admin: schemas.AdminRegister, db: Session = Depends(get_db)):
    return crud.admin_register(db, admin)


@admin_router.post("/login")
def admin_login(login: schemas.AdminLogin, db: Session = Depends(get_db)):
    return crud.admin_login(db, login)


@admin_router.get("/customers")
def list_customers(
    _: models.Admin = Depends(require_admin),
    db: Session = Depends(get_db)
):
    customers = crud.get_all_customers(db)
    return [
        {
            "id": c.cust_id,
            "name": c.cust_name,
            "email": c.cust_mail,
            "phone": c.cust_phoneno,
            "kyc_approved": c.kyc_approved
        } for c in customers
    ]


@admin_router.patch("/customer/{cust_id}/kyc")
def change_kyc_status(
    cust_id: int,
    data: schemas.KycStatusUpdate,
    _: models.Admin = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return crud.update_kyc_status(db, cust_id, data)


def get_current_customer(
    x_cust_id: int = Header(..., alias="X-Customer-ID"),
    db: Session = Depends(get_db)
):
    cust = db.query(models.Customer).filter(models.Customer.cust_id == x_cust_id).first()
    if not cust:
        raise HTTPException(status_code=401, detail="Invalid customer")
    return cust


# ACCOUNT ENDPOINTS
@customer_router.post("/account", response_model=schemas.AccountResponse,
                      status_code=http_status.HTTP_201_CREATED)
def open_account(
    payload: schemas.AccountCreate,
    cust: models.Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Customer opens a new bank account.
    Header: X-Customer-ID: <id>
    """
    account = crud.create_account(db, cust_id=cust.cust_id, payload=payload)
    return account


@customer_router.get("/accounts")
def list_my_accounts(
    cust: models.Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    accounts = db.query(models.Account).filter(models.Account.cust_id == cust.cust_id).all()
    return [
        {
            "acc_no": a.acc_no,
            "type": a.type,
            "balance": float(a.balance),
            "nominee": a.nominee_name,
            "created_at": a.created_at
        } for a in accounts
    ]


# TRANSFER ENDPOINT
@customer_router.post("/transfer", response_model=schemas.TransferResponse)
def transfer(
    payload: schemas.TransferRequest,
    cust: models.Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Transfer money between any two accounts (same bank).
    Header: X-Customer-ID: <id>
    """
    sender_acc = db.query(models.Account).filter(
        models.Account.acc_no == payload.from_acc_no
    ).first()
    if not sender_acc or sender_acc.cust_id != cust.cust_id:
        raise HTTPException(status_code=403, detail="You can only transfer from your own account")

    return crud.transfer_money(db, payload)
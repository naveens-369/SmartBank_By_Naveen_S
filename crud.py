# crud.py
from sqlalchemy.orm import Session
import models, schemas
from fastapi import HTTPException, status
# crud.py (only changed parts)
from auth import verify_password, get_password_hash, create_access_token
import random, string
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_

# Customer
# register
def cust_register(db: Session, user: schemas.Register):
    if db.query(models.Customer).filter(models.Customer.cust_mail == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.Customer).filter(models.Customer.cust_phoneno == user.phoneno).first():
        raise HTTPException(status_code=400, detail="Phone already registered")

    hashed_password = get_password_hash(user.password)
    db_user = models.Customer(
        cust_name=user.name,
        cust_phoneno=user.phoneno,
        cust_age=user.age,
        cust_address=user.address,
        cust_mail=user.email,
        cust_password=hashed_password,
        kyc_approved=0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Registered Successfully"}

# login
def cust_login(db: Session, login: schemas.Login):
    # check customer email already exists
    user = db.query(models.Customer).filter(models.Customer.cust_mail == login.email).first()
    if user and user.cust_password != login.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    if not user or user.cust_password != login.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.cust_id, "name": user.cust_name, "role": "customer"})
    return {
        "message": f"Welcome {user.cust_name}!",
        "cust_id": user.cust_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

# upload kyc
def upload_kyc(db: Session, cust_id: int, aadhar: str, pan: str, kyc_doc):
    # check customer id already exists
    cust = db.query(models.Customer).filter(models.Customer.cust_id == cust_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    # check kyc uploaded or not
    if db.query(models.KYC).filter(models.KYC.cust_id == cust_id).first():
        raise HTTPException(status_code=400, detail="KYC already uploaded")

    new_kyc = models.KYC(
        cust_id=cust_id,
        aadhar_card=aadhar,
        pan_card=pan,
        kyc_doc=kyc_doc.file.read()
    )
    db.add(new_kyc)
    db.commit()
    db.refresh(new_kyc)
    return {"message": "KYC Uploaded Successfully"}


# Admin
# register
def admin_register(db: Session, admin: schemas.AdminRegister):
    # check customer email already exists
    if db.query(models.Admin).filter(models.Admin.admin_email == admin.email).first():
        raise HTTPException(status_code=400, detail="Admin already exists")

    new_admin = models.Admin(
        admin_name=admin.name,
        admin_email=admin.email,
        admin_password=admin.password
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"message": "Admin registered successfully"}

# login
def admin_login(db: Session, login: schemas.AdminLogin):
    # check customer email already exists
    admin = db.query(models.Admin).filter(models.Admin.admin_email == login.email).first()
    if admin and admin.admin_password != login.password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    if not admin or admin.admin_password != login.password:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    access_token = create_access_token(data={"sub": admin.admin_id, "role": "admin"})
    return {
        "message": f"Welcome {admin.admin_name}!",
        "admin_id": admin.admin_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

# manage customer details
def get_all_customers(db: Session):
    return db.query(models.Customer).all()

# approve kyc status
def update_kyc_status(db: Session, cust_id: int, data: schemas.KycStatusUpdate):
    # check customer id
    cust = db.query(models.Customer).filter(models.Customer.cust_id == cust_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    cust.kyc_approved = data.approved
    db.commit()
    db.refresh(cust)
    return {
        "message": f"KYC {'APPROVED' if data.approved else 'REJECTED'} for {cust.cust_name}",
        "cust_id": cust_id,
        "approved": data.approved
    }

# generate transactions id
def _generate_txn_id(db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"TRX-{today}"
    # count how many transactions exist for today
    count = db.query(models.Transaction).filter(
        models.Transaction.txn_id.like(f"{prefix}-%")
    ).count()
    suffix = f"{count+1:05d}"
    return f"{prefix}-{suffix}"

# Open new account
def create_account(db: Session, cust_id: int, payload: schemas.AccountCreate):
    # validate customer exists
    cust = db.query(models.Customer).filter(models.Customer.cust_id == cust_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    # KYC must be approved for any account
    if not cust.kyc_approved:
        raise HTTPException(status_code=403, detail="KYC not approved")

    # Minimum initial deposit rules
    min_deposit = {
        "savings": Decimal("500"),
        "current": Decimal("1000"),
        "fd": Decimal("5000")
    }
    required = min_deposit.get(payload.type, Decimal("0"))
    if Decimal(str(payload.initial_deposit)) < required:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum initial deposit for {payload.type} is ₹{required}"
        )

    # generate unique acc_no
    acc_no = _generate_acc_no(db)

    new_acc = models.Account(
        acc_no=acc_no,
        type=payload.type,
        balance=Decimal(str(payload.initial_deposit)),
        nominee_name=payload.nominee_name,
        cust_id=cust_id
    )
    db.add(new_acc)
    db.commit()
    db.refresh(new_acc)

    # log the opening deposit as a transaction
    txn = models.Transaction(
        txn_id=_generate_txn_id(db),
        from_acc_no=None,
        to_acc_no=acc_no,
        amount=Decimal(str(payload.initial_deposit)),
        txn_type="deposit",
        status="SUCCESS"
    )
    db.add(txn)
    db.commit()

    return new_acc


# Transfer money
DAILY_LIMIT = Decimal("50000")      # ₹50,000 per day per account

def transfer_money(db: Session, payload: schemas.TransferRequest):
    amount = Decimal(str(payload.amount))

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # fetch accounts
    from_acc = db.query(models.Account).filter(models.Account.acc_no == payload.from_acc_no).first()
    to_acc   = db.query(models.Account).filter(models.Account.acc_no == payload.to_acc_no).first()

    if not from_acc or not to_acc:
        raise HTTPException(status_code=404, detail="One or both accounts not found")

    if from_acc.acc_no == to_acc.acc_no:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    # KYC check for sender
    sender = db.query(models.Customer).filter(models.Customer.cust_id == from_acc.cust_id).first()
    if not sender.kyc_approved:
        raise HTTPException(status_code=403, detail="Sender KYC not approved")

    # check Balance
    if from_acc.balance < amount:
        _log_failed(db, payload.from_acc_no, payload.to_acc_no, amount, "INSUFFICIENT_FUNDS")
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Daily limit check
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day   = start_of_day + timedelta(days=1)

    daily_total = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.from_acc_no == payload.from_acc_no,
        models.Transaction.txn_type == "transfer",
        models.Transaction.status == "SUCCESS",
        models.Transaction.timestamp >= start_of_day,
        models.Transaction.timestamp < end_of_day
    ).scalar() or Decimal("0")

    if daily_total + amount > DAILY_LIMIT:
        _log_failed(db, payload.from_acc_no, payload.to_acc_no, amount, "DAILY_LIMIT_EXCEEDED")
        raise HTTPException(status_code=400,
                            detail=f"Daily transfer limit of ₹{DAILY_LIMIT} exceeded")

    # Perform transfer
    try:
        from_acc.balance -= amount
        to_acc.balance   += amount

        txn = models.Transaction(
            txn_id=_generate_txn_id(db),
            from_acc_no=payload.from_acc_no,
            to_acc_no=payload.to_acc_no,
            amount=amount,
            txn_type="transfer",
            status="SUCCESS"
        )
        db.add(txn)
        db.commit()
    except Exception as e:
        db.rollback()
        _log_failed(db, payload.from_acc_no, payload.to_acc_no, amount, "SYSTEM_ERROR")
        raise HTTPException(status_code=500, detail="Transfer failed – please try again")

    return {
        "txn_id": txn.txn_id,
        "amount": float(amount),
        "status": "SUCCESS",
        "timestamp": txn.timestamp
    }


def _log_failed(db: Session, from_acc, to_acc, amount, reason):
    """Utility to log failed attempts useful for audit / fraud detection"""
    txn = models.Transaction(
        txn_id=_generate_txn_id(db),
        from_acc_no=from_acc,
        to_acc_no=to_acc,
        amount=amount,
        txn_type="transfer",
        status="FAILED",
        # you can add a column `reason` if you want
    )
    db.add(txn)
    db.commit()

def _generate_acc_no(db: Session) -> int:
    while True:
        acc_no = random.randint(1000_0000_0000, 9999_9999_9999)  # 12-digit number
        if not db.query(models.Account).filter(models.Account.acc_no == acc_no).first():
            return acc_no
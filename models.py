from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, BIGINT, LargeBinary, ForeignKey,
    Boolean, DateTime, Numeric, CheckConstraint
)
from sqlalchemy.dialects.mysql import LONGBLOB, DECIMAL
from db import Base

class Customer(Base):
    __tablename__ = "customers"

    cust_id       = Column(Integer, primary_key=True, index=True)
    cust_password = Column(String(255), nullable=False)
    cust_name     = Column(String(50), index=True, nullable=False)
    cust_phoneno  = Column(BIGINT, unique=True, nullable=False)
    cust_address  = Column(String(100))
    cust_age      = Column(Integer)
    cust_mail     = Column(String(50), unique=True, index=True, nullable=False)
    # KYC Status (managed by admin)
    kyc_approved  = Column(Integer, default=False, nullable=False)


class KYC(Base):
    __tablename__ = "kyc"

    kyc_id      = Column(Integer, primary_key=True, index=True)
    aadhar_card = Column(String(19), unique=True, nullable=False)
    pan_card    = Column(String(19), index=True, nullable=False)
    kyc_doc     = Column(LONGBLOB, nullable=False)
    cust_id     = Column(Integer, ForeignKey("customers.cust_id", ondelete="CASCADE"))


class Admin(Base):
    __tablename__ = "admin"

    admin_id       = Column(Integer, primary_key=True, index=True)
    admin_name     = Column(String(50), nullable=False)
    admin_email    = Column(String(50), unique=True, index=True, nullable=False)
    admin_password = Column(String(255), nullable=False)


class Account(Base):
    __tablename__ = "accounts"

    id            = Column(Integer, primary_key=True, index=True)
    acc_no        = Column(BIGINT, unique=True, nullable=False, index=True)
    type          = Column(String(20), nullable=False)        
    balance       = Column(DECIMAL(15, 2), default=0.0, nullable=False)
    nominee_name  = Column(String(50), nullable=False)
    cust_id       = Column(Integer, ForeignKey("customers.cust_id", ondelete="CASCADE"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("type IN ('savings','current','fd')", name="valid_account_type"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id            = Column(Integer, primary_key=True, index=True)
    txn_id        = Column(String(30), unique=True, nullable=False, index=True) 
    from_acc_no   = Column(BIGINT, ForeignKey("accounts.acc_no", ondelete="CASCADE"))
    to_acc_no     = Column(BIGINT, ForeignKey("accounts.acc_no", ondelete="CASCADE"))
    amount        = Column(DECIMAL(15, 2), nullable=False)
    txn_type      = Column(String(20), nullable=False)   
    timestamp   = Column(DateTime, default=datetime.utcnow, nullable=False)
    status        = Column(String(10), default="SUCCESS", nullable=False)  
A **secure banking system** built with **Python**, **FastAPI**, **SQLAlchemy**, and **MySQL**. Features include:

- Customer registration & login
- KYC upload & admin approval
- Account creation (Savings, Current, FD)
- Secure money transfer with daily limits
- Admin panel for customer & KYC management

---

## Features

| Feature | Description |
|-------|-----------|
| **Customer Auth** | Register, Login |
| **KYC Verification** | Upload Aadhaar, PAN, Document |
| **Account Management** | Open Savings/Current/FD accounts |
| **Money Transfer** | Secure transfers with ₹50,000 daily limit |
| **Admin Panel** | View customers, approve/reject KYC |
| **Transaction Logging** | Full audit trail (success + failed attempts) |

---

## Tech Stack

- **FastAPI** – API Framework
- **SQLAlchemy** – ORM
- **MySQL** – Database
- **Pydantic** – Data Validation
- **Python 3.9+**

---

## Steps
- Clone the code into the VS code by clicking Clone Git Repository and paste web URL.
- Create a **.env** file containing Database host, Database port, Database name(Here I should smart_bank), Database Password and Database User
- Install packages
    - **pip install pydantic**
    - **pip install pymysql sqlalchemy mysql-connector-python databases dotenv**
    - **pip install fastapi uvicorn**
- Run **uvicorn main:app --reload** and Open **http://127.0.0.1:8000/docs**
 

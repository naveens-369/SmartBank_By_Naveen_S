# tests/test_admin_kyc.py
from schemas import KycStatusUpdate
import crud

def test_admin_approve_kyc(client, db_session):
    # 1. Register a customer
    client.post("/customers/register", json={
        "name": "Neha", "phoneno": 9988776655, "age": 27,
        "address": "Delhi", "email": "neha@example.com", "password": "pwd"
    })
    login = client.post("/customers/login", json={"email":"neha@example.com","password":"pwd"}).json()
    cust_id = login["cust_id"]

    # 2. Register an admin
    client.post("/admin/register", json={
        "name": "Super Admin", "email": "admin@bank.com", "password": "admin123"
    })
    admin = client.post("/admin/login", json={"email":"admin@bank.com","password":"admin123"}).json()
    admin_id = admin["admin_id"]

    # 3. Approve KYC
    resp = client.patch(f"/admin/customer/{cust_id}/kyc",
                        json={"approved": True},
                        headers={"X-Admin-ID": str(admin_id)})
    assert resp.status_code == 200
    assert resp.json()["message"] == "KYC APPROVED for Neha"

    # 4. Verify DB flag
    cust = db_session.query(models.Customer).filter(models.Customer.cust_id == cust_id).first()
    assert cust.kyc_approved == 1
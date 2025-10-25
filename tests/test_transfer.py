# tests/test_transfer.py
from decimal import Decimal

def _open_account(client, cust_id, deposit):
    resp = client.post("/customers/account", json={
        "type": "savings",
        "nominee_name": "Nom",
        "initial_deposit": deposit
    }, headers={"X-Customer-ID": str(cust_id)})
    assert resp.status_code == 201
    return resp.json()["acc_no"]

def _setup_two_accounts(client, db_session):
    # Customer A
    client.post("/customers/register", json={
        "name":"A","phoneno":9000000001,"age":30,"address":"X",
        "email":"a@example.com","password":"pwd"
    })
    a_login = client.post("/customers/login", json={"email":"a@example.com","password":"pwd"}).json()
    a_id = a_login["cust_id"]
    crud.update_kyc_status(db_session, a_id, schemas.KycStatusUpdate(approved=True))
    acc_a = _open_account(client, a_id, 100000)

    # Customer B
    client.post("/customers/register", json={
        "name":"B","phoneno":9000000002,"age":30,"address":"Y",
        "email":"b@example.com","password":"pwd"
    })
    b_login = client.post("/customers/login", json={"email":"b@example.com","password":"pwd"}).json()
    b_id = b_login["cust_id"]
    crud.update_kyc_status(db_session, b_id, schemas.KycStatusUpdate(approved=True))
    acc_b = _open_account(client, b_id, 5000)

    return (a_id, acc_a), (b_id, acc_b)

def test_transfer_success_and_daily_limit(client, db_session):
    (a_id, acc_a), (_, acc_b) = _setup_two_accounts(client, db_session)

    # ---- SUCCESS (under limit) ----
    resp = client.post("/customers/transfer", json={
        "from_acc_no": acc_a,
        "to_acc_no": acc_b,
        "amount": 45000
    }, headers={"X-Customer-ID": str(a_id)})
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCESS"

    # ---- DAILY LIMIT EXCEEDED ----
    resp = client.post("/customers/transfer", json={
        "from_acc_no": acc_a,
        "to_acc_no": acc_b,
        "amount": 10000   # 45k + 10k > 50k
    }, headers={"X-Customer-ID": str(a_id)})
    assert resp.status_code == 400
    assert "DAILY_LIMIT_EXCEEDED" in resp.json()["detail"]

    # ---- FAILED LOGGED ----
    failed = db_session.query(models.Transaction)\
        .filter(models.Transaction.status == "FAILED").first()
    assert failed is not None
    assert failed.txn_type == "transfer"
    assert failed.amount == Decimal("10000")
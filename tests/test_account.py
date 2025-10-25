# tests/test_account.py
def _register_and_approve(client, db_session, email, phone):
    client.post("/customers/register", json={
        "name": email.split("@")[0], "phoneno": phone, "age": 30,
        "address": "Test", "email": email, "password": "pwd"
    })
    login = client.post("/customers/login", json={"email":email,"password":"pwd"}).json()
    cust_id = login["cust_id"]

    # Approve KYC directly (no BLOB)
    from crud import update_kyc_status
    update_kyc_status(db_session, cust_id, KycStatusUpdate(approved=True))
    return cust_id, login["cust_id"]

def test_account_creation_rules(client, db_session):
    cust_id, _ = _register_and_approve(client, db_session, "acc@example.com", 9111122223)

    # Minimum deposit checks
    cases = [
        ("savings", 499, 400),   # < 500 → fail
        ("savings", 500, 201),   # OK
        ("current", 999, 400),   # < 1000 → fail
        ("current", 1000, 201),  # OK
        ("fd", 4999, 400),       # < 5000 → fail
        ("fd", 5000, 201),       # OK
    ]

    for acc_type, deposit, expected in cases:
        resp = client.post("/customers/account", json={
            "type": acc_type,
            "nominee_name": "Nominee",
            "initial_deposit": deposit
        }, headers={"X-Customer-ID": str(cust_id)})

        assert resp.status_code == expected, f"{acc_type} ₹{deposit}"
        if expected == 201:
            data = resp.json()
            assert data["balance"] == float(deposit)
            assert data["type"] == acc_type
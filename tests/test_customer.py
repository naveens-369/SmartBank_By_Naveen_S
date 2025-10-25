def test_register_and_login_with_jwt(client):
    # Register
    client.post("/customers/register", json={
        "name": "Vikram", "phoneno": 9123456789, "age": 32,
        "address": "Mumbai", "email": "vikram@example.com", "password": "secret123"
    })

    # Login → get token
    resp = client.post("/customers/login", json={
        "email": "vikram@example.com", "password": "secret123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    token = data["access_token"]

    # Use token in protected route
    resp = client.post("/customers/account", json={
        "type": "savings",
        "nominee_name": "Ravi",
        "initial_deposit": 500
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
import uuid


def build_product_payload(name: str | None = None):
    base_name = name or f"Laptop{uuid.uuid4().hex[:8]}"
    return {
        "name": base_name,
        "price": 150.0,
        "available_quantity": 10,
        "category_id": 1,
    }


def test_get_products_returns_list(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_product_creates_record_and_history(client):
    payload = build_product_payload()

    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == payload["name"]

    product_id = body["id"]
    history_response = client.get(f"/api/v1/products/{product_id}/history")
    assert history_response.status_code == 200, history_response.text
    entries = history_response.json()
    assert len(entries) == 1
    assert entries[0]["action"] == "CREATE"
    assert entries[0]["previous_state"] is None
    assert entries[0]["current_state"]["name"] == payload["name"]


def test_post_product_rejects_banned_name(client):
    payload = build_product_payload("Scam")

    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 422, response.text
    assert "forbidden" in response.json()["detail"].lower()


def test_put_product_updates_record_and_history(client):
    payload = build_product_payload()
    created = client.post("/api/v1/products", json=payload)
    product_id = created.json()["id"]

    updated_payload = {
        "name": f"Desk{uuid.uuid4().hex[:6]}",
        "price": 1200.0,
        "available_quantity": 5,
        "category_id": 2,
    }

    response = client.put(f"/api/v1/products/{product_id}", json=updated_payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["price"] == 1200.0
    assert body["category"]["id"] == 2

    history_response = client.get(f"/api/v1/products/{product_id}/history")
    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    replace_entry = next(entry for entry in history if entry["action"] == "REPLACE")
    assert replace_entry["previous_state"]["name"] == payload["name"]
    assert replace_entry["previous_state"]["price"] == payload["price"]
    assert replace_entry["current_state"]["name"] == updated_payload["name"]
    assert replace_entry["current_state"]["price"] == updated_payload["price"]
    assert replace_entry["current_state"]["available_quantity"] == 5
    assert replace_entry["current_state"]["category"]["id"] == 2


def test_patch_and_delete_are_recorded_in_history(client):
    created = client.post("/api/v1/products", json=build_product_payload())
    assert created.status_code == 201, created.text
    product = created.json()
    product_id = product["id"]

    patch_response = client.patch(
        f"/api/v1/products/{product_id}",
        json={"available_quantity": 3},
    )
    assert patch_response.status_code == 200, patch_response.text

    delete_response = client.delete(f"/api/v1/products/{product_id}")
    assert delete_response.status_code == 204, delete_response.text

    history_response = client.get(f"/api/v1/products/{product_id}/history")
    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    actions = [entry["action"] for entry in history]
    assert actions == ["DELETE", "UPDATE", "CREATE"]
    assert history[1]["previous_state"]["available_quantity"] == 10
    assert history[1]["current_state"]["available_quantity"] == 3
    assert history[0]["previous_state"]["available_quantity"] == 3
    assert history[0]["current_state"] is None

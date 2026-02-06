def test_get_players_empty(client):
    response = client.get("/api/players")
    assert response.status_code == 200
    assert response.json() == []


def test_create_player(client):
    response = client.post("/api/players", json={
        "name": "John Smith",
        "nickname": "Smithy",
        "usual_number": "10"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Smith"
    assert data["nickname"] == "Smithy"
    assert data["usual_number"] == "10"
    assert "id" in data
    assert "created_at" in data


def test_create_player_minimal(client):
    response = client.post("/api/players", json={"name": "Jane Doe"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["nickname"] is None
    assert data["usual_number"] is None


def test_create_player_missing_name(client):
    response = client.post("/api/players", json={"nickname": "Ghost"})
    assert response.status_code == 422


def test_get_players_returns_created(client):
    client.post("/api/players", json={"name": "Alice", "usual_number": "7"})
    client.post("/api/players", json={"name": "Bob", "usual_number": "9"})

    response = client.get("/api/players")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [p["name"] for p in data]
    assert "Alice" in names
    assert "Bob" in names

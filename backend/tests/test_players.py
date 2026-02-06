def test_get_players_empty(client):
    response = client.get("/api/players")
    assert response.status_code == 200
    assert response.json() == []

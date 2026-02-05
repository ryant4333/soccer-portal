# Jersey Tracker Phase 2: Backend Players CRUD

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement full CRUD for the players resource with TDD

**Architecture:** FastAPI router at /api/players with all CRUD endpoints. SQLAlchemy models for DB access, Pydantic schemas for request/response validation. All endpoints tested with pytest + httpx TestClient against an in-memory SQLite database.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, pytest, httpx

**Prerequisite Plans:** Phase 1 (Project Scaffolding & Docker) must be complete

---

## Task 1: Create players router and register it

**Files:**
- Create: `backend/app/routers/players.py`
- Modify: `backend/app/main.py`

**Step 1: Write the empty router**

Create `backend/app/routers/players.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/players", tags=["players"])
```

**Step 2: Register the router in main.py**

Add to `backend/app/main.py` after the health endpoint:

```python
from app.routers import players

app.include_router(players.router)
```

**Step 3: Commit**

```bash
git add backend/app/routers/players.py backend/app/main.py
git commit -m "chore: add empty players router and register in app"
```

---

## Task 2: TDD — GET /api/players (empty list)

**Files:**
- Create: `backend/tests/test_players.py`
- Modify: `backend/app/routers/players.py`

**Step 1: Write the failing test**

Create `backend/tests/test_players.py`:

```python
def test_get_players_empty(client):
    response = client.get("/api/players")
    assert response.status_code == 200
    assert response.json() == []
```

**Step 2: Run the test to verify it fails**

```bash
cd backend && python -m pytest tests/test_players.py::test_get_players_empty -v
```

Expected: FAIL — 404 (no route defined yet)

**Step 3: Implement the GET endpoint**

Update `backend/app/routers/players.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player
from app.schemas import PlayerResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("", response_model=list[PlayerResponse])
def get_players(db: Session = Depends(get_db)):
    return db.query(Player).all()
```

**Step 4: Run the test to verify it passes**

```bash
cd backend && python -m pytest tests/test_players.py::test_get_players_empty -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_players.py backend/app/routers/players.py
git commit -m "feat: add GET /api/players endpoint with test"
```

---

## Task 3: TDD — POST /api/players

**Files:**
- Modify: `backend/tests/test_players.py`
- Modify: `backend/app/routers/players.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_players.py`:

```python
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
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_players.py::test_create_player -v
```

Expected: FAIL — 405 Method Not Allowed (no POST route)

**Step 3: Implement the POST endpoint**

Add to `backend/app/routers/players.py`:

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player
from app.schemas import PlayerCreate, PlayerResponse

# ... existing router and GET endpoint ...

@router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    db_player = Player(
        name=player.name,
        nickname=player.nickname,
        usual_number=player.usual_number,
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player
```

**Step 4: Run all tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_players.py -v
```

Expected: All 4 tests PASS (empty list, create full, create minimal, missing name)

**Step 5: Commit**

```bash
git add backend/tests/test_players.py backend/app/routers/players.py
git commit -m "feat: add POST /api/players endpoint with tests"
```

---

## Task 4: TDD — GET /api/players returns created players

**Files:**
- Modify: `backend/tests/test_players.py`

**Step 1: Write the test**

Add to `backend/tests/test_players.py`:

```python
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
```

**Step 2: Run the test to verify it passes**

```bash
cd backend && python -m pytest tests/test_players.py::test_get_players_returns_created -v
```

Expected: PASS (already implemented)

**Step 3: Commit**

```bash
git add backend/tests/test_players.py
git commit -m "test: add test verifying GET /api/players returns created players"
```

---

## Task 5: TDD — PUT /api/players/{id}

**Files:**
- Modify: `backend/tests/test_players.py`
- Modify: `backend/app/routers/players.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_players.py`:

```python
def test_update_player(client):
    create_resp = client.post("/api/players", json={"name": "Old Name", "usual_number": "5"})
    player_id = create_resp.json()["id"]

    response = client.put(f"/api/players/{player_id}", json={"name": "New Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["usual_number"] == "5"  # unchanged field preserved


def test_update_player_not_found(client):
    response = client.put("/api/players/999", json={"name": "Ghost"})
    assert response.status_code == 404
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_players.py::test_update_player -v
```

Expected: FAIL — 405 Method Not Allowed

**Step 3: Implement the PUT endpoint**

Add to `backend/app/routers/players.py` (also add `HTTPException` to imports):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Player
from app.schemas import PlayerCreate, PlayerResponse, PlayerUpdate

# ... existing endpoints ...

@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(player_id: int, player: PlayerUpdate, db: Session = Depends(get_db)):
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    if player.name is not None:
        db_player.name = player.name
    if player.nickname is not None:
        db_player.nickname = player.nickname
    if player.usual_number is not None:
        db_player.usual_number = player.usual_number
    db.commit()
    db.refresh(db_player)
    return db_player
```

**Step 4: Run the tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_players.py::test_update_player tests/test_players.py::test_update_player_not_found -v
```

Expected: Both PASS

**Step 5: Commit**

```bash
git add backend/tests/test_players.py backend/app/routers/players.py
git commit -m "feat: add PUT /api/players/{id} endpoint with tests"
```

---

## Task 6: TDD — DELETE /api/players/{id}

**Files:**
- Modify: `backend/tests/test_players.py`
- Modify: `backend/app/routers/players.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_players.py`:

```python
def test_delete_player(client):
    create_resp = client.post("/api/players", json={"name": "To Delete"})
    player_id = create_resp.json()["id"]

    response = client.delete(f"/api/players/{player_id}")
    assert response.status_code == 204

    # Verify player is gone
    get_resp = client.get("/api/players")
    names = [p["name"] for p in get_resp.json()]
    assert "To Delete" not in names


def test_delete_player_not_found(client):
    response = client.delete("/api/players/999")
    assert response.status_code == 404
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_players.py::test_delete_player -v
```

Expected: FAIL — 405 Method Not Allowed

**Step 3: Implement the DELETE endpoint**

Add to `backend/app/routers/players.py`:

```python
from fastapi import Response

# ... existing endpoints ...

@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, db: Session = Depends(get_db)):
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    db.delete(db_player)
    db.commit()
```

**Step 4: Run the tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_players.py::test_delete_player tests/test_players.py::test_delete_player_not_found -v
```

Expected: Both PASS

**Step 5: Commit**

```bash
git add backend/tests/test_players.py backend/app/routers/players.py
git commit -m "feat: add DELETE /api/players/{id} endpoint with tests"
```

---

## Task 7: Run full test suite

**Step 1: Run all tests**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass (health + all player CRUD tests)

**Step 2: Commit any fixes if needed**

```bash
git add backend/
git commit -m "fix: resolve any issues from full test suite run"
```

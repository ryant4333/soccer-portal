# Jersey Tracker Phase 3: Backend Jersey Wash Logic

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement jersey wash tracking endpoints — record handoffs, query current holder, list roster sorted by fewest washes, and undo accidental handoffs

**Architecture:** FastAPI router at /api/jerseys. Business logic: current holder is the most recent jersey_washes row; roster is a LEFT JOIN of players to jersey_washes grouped and sorted by count ascending. Append-only handoff recording with delete for undo.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, pytest, httpx

**Prerequisite Plans:** Phase 1 (Scaffolding) and Phase 2 (Players CRUD) must be complete

---

## Task 1: Create jerseys router and register it

**Files:**
- Create: `backend/app/routers/jerseys.py`
- Modify: `backend/app/main.py`

**Step 1: Write the empty router**

Create `backend/app/routers/jerseys.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/jerseys", tags=["jerseys"])
```

**Step 2: Register the router in main.py**

Add to `backend/app/main.py`:

```python
from app.routers import players, jerseys

app.include_router(players.router)
app.include_router(jerseys.router)
```

**Step 3: Commit**

```bash
git add backend/app/routers/jerseys.py backend/app/main.py
git commit -m "chore: add empty jerseys router and register in app"
```

---

## Task 2: TDD — POST /api/jerseys (record handoff)

**Files:**
- Create: `backend/tests/test_jerseys.py`
- Modify: `backend/app/routers/jerseys.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_jerseys.py`:

```python
def _create_player(client, name="Test Player", usual_number="10"):
    """Helper to create a player and return the response data."""
    resp = client.post("/api/players", json={"name": name, "usual_number": usual_number})
    assert resp.status_code == 201
    return resp.json()


def test_record_handoff(client):
    player = _create_player(client)

    response = client.post("/api/jerseys", json={"player_id": player["id"]})
    assert response.status_code == 201
    data = response.json()
    assert data["player_id"] == player["id"]
    assert "id" in data
    assert "taken_at" in data


def test_record_handoff_nonexistent_player(client):
    response = client.post("/api/jerseys", json={"player_id": 999})
    assert response.status_code == 404
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_jerseys.py::test_record_handoff -v
```

Expected: FAIL — 405 Method Not Allowed (no POST route)

**Step 3: Implement the POST endpoint**

Update `backend/app/routers/jerseys.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JerseyWash, Player
from app.schemas import JerseyWashCreate, JerseyWashResponse

router = APIRouter(prefix="/api/jerseys", tags=["jerseys"])


@router.post("", response_model=JerseyWashResponse, status_code=status.HTTP_201_CREATED)
def record_handoff(wash: JerseyWashCreate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == wash.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    db_wash = JerseyWash(player_id=wash.player_id)
    db.add(db_wash)
    db.commit()
    db.refresh(db_wash)
    return db_wash
```

**Step 4: Run the tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_jerseys.py -v
```

Expected: Both PASS

**Step 5: Commit**

```bash
git add backend/tests/test_jerseys.py backend/app/routers/jerseys.py
git commit -m "feat: add POST /api/jerseys endpoint to record handoffs"
```

---

## Task 3: TDD — GET /api/jerseys/current

**Files:**
- Modify: `backend/tests/test_jerseys.py`
- Modify: `backend/app/routers/jerseys.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_jerseys.py`:

```python
def test_get_current_holder_none(client):
    response = client.get("/api/jerseys/current")
    assert response.status_code == 200
    assert response.json() is None


def test_get_current_holder(client):
    player = _create_player(client, name="Alice", usual_number="7")
    client.post("/api/jerseys", json={"player_id": player["id"]})

    response = client.get("/api/jerseys/current")
    assert response.status_code == 200
    data = response.json()
    assert data["player"]["name"] == "Alice"
    assert "taken_at" in data
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_jerseys.py::test_get_current_holder_none -v
```

Expected: FAIL — 404 (no route)

**Step 3: Implement the GET /current endpoint**

Add to `backend/app/routers/jerseys.py` (must be defined BEFORE any `/{id}` routes):

```python
from typing import Optional

from app.schemas import CurrentHolder, JerseyWashCreate, JerseyWashResponse, PlayerResponse

# ... existing imports and router ...

@router.get("/current", response_model=Optional[CurrentHolder])
def get_current_holder(db: Session = Depends(get_db)):
    wash = db.query(JerseyWash).order_by(JerseyWash.taken_at.desc()).first()
    if not wash:
        return None
    player = db.query(Player).filter(Player.id == wash.player_id).first()
    return CurrentHolder(
        player=PlayerResponse.model_validate(player),
        taken_at=wash.taken_at,
    )
```

**Step 4: Run the tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_jerseys.py::test_get_current_holder_none tests/test_jerseys.py::test_get_current_holder -v
```

Expected: Both PASS

**Step 5: Commit**

```bash
git add backend/tests/test_jerseys.py backend/app/routers/jerseys.py
git commit -m "feat: add GET /api/jerseys/current endpoint"
```

---

## Task 4: TDD — GET /api/jerseys (roster sorted by fewest washes)

**Files:**
- Modify: `backend/tests/test_jerseys.py`
- Modify: `backend/app/routers/jerseys.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_jerseys.py`:

```python
def test_get_roster_empty(client):
    response = client.get("/api/jerseys")
    assert response.status_code == 200
    data = response.json()
    assert data["current_holder"] is None
    assert data["roster"] == []


def test_get_roster_sorted_by_fewest_washes(client):
    alice = _create_player(client, name="Alice", usual_number="7")
    bob = _create_player(client, name="Bob", usual_number="9")
    charlie = _create_player(client, name="Charlie", usual_number="3")

    # Alice washes 2 times, Bob 1 time, Charlie 0 times
    client.post("/api/jerseys", json={"player_id": alice["id"]})
    client.post("/api/jerseys", json={"player_id": alice["id"]})
    client.post("/api/jerseys", json={"player_id": bob["id"]})

    response = client.get("/api/jerseys")
    assert response.status_code == 200
    data = response.json()

    roster = data["roster"]
    assert len(roster) == 3

    # Sorted by fewest washes: Charlie (0), Bob (1), Alice (2)
    assert roster[0]["player"]["name"] == "Charlie"
    assert roster[0]["wash_count"] == 0
    assert roster[1]["player"]["name"] == "Bob"
    assert roster[1]["wash_count"] == 1
    assert roster[2]["player"]["name"] == "Alice"
    assert roster[2]["wash_count"] == 2

    # Current holder is Bob (most recent handoff)
    assert data["current_holder"]["player"]["name"] == "Bob"


def test_get_roster_player_with_zero_washes(client):
    _create_player(client, name="NewPlayer", usual_number="99")

    response = client.get("/api/jerseys")
    data = response.json()
    assert len(data["roster"]) == 1
    assert data["roster"][0]["player"]["name"] == "NewPlayer"
    assert data["roster"][0]["wash_count"] == 0
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_jerseys.py::test_get_roster_empty -v
```

Expected: FAIL — current GET /api/jerseys doesn't exist or returns wrong format

**Step 3: Implement the GET /api/jerseys endpoint**

Add to `backend/app/routers/jerseys.py`:

```python
from pydantic import BaseModel
from sqlalchemy import func

from app.schemas import CurrentHolder, JerseyRosterEntry, JerseyWashCreate, JerseyWashResponse, PlayerResponse


class JerseyDataResponse(BaseModel):
    current_holder: Optional[CurrentHolder]
    roster: list[JerseyRosterEntry]


@router.get("", response_model=JerseyDataResponse)
def get_jersey_data(db: Session = Depends(get_db)):
    # Current holder
    latest_wash = db.query(JerseyWash).order_by(JerseyWash.taken_at.desc()).first()
    current_holder = None
    if latest_wash:
        holder_player = db.query(Player).filter(Player.id == latest_wash.player_id).first()
        current_holder = CurrentHolder(
            player=PlayerResponse.model_validate(holder_player),
            taken_at=latest_wash.taken_at,
        )

    # Roster: all players with wash counts, sorted by fewest washes
    wash_counts = (
        db.query(JerseyWash.player_id, func.count(JerseyWash.id).label("wash_count"))
        .group_by(JerseyWash.player_id)
        .subquery()
    )
    players = db.query(Player).all()
    count_map = {
        row.player_id: row.wash_count
        for row in db.query(wash_counts).all()
    }
    roster = [
        JerseyRosterEntry(
            player=PlayerResponse.model_validate(p),
            wash_count=count_map.get(p.id, 0),
        )
        for p in players
    ]
    roster.sort(key=lambda entry: entry.wash_count)

    return JerseyDataResponse(current_holder=current_holder, roster=roster)
```

**Step 4: Run the tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_jerseys.py -v
```

Expected: All jersey tests PASS

**Step 5: Commit**

```bash
git add backend/tests/test_jerseys.py backend/app/routers/jerseys.py
git commit -m "feat: add GET /api/jerseys endpoint with roster sorted by fewest washes"
```

---

## Task 5: TDD — DELETE /api/jerseys/{id} (undo handoff)

**Files:**
- Modify: `backend/tests/test_jerseys.py`
- Modify: `backend/app/routers/jerseys.py`

**Step 1: Write the failing tests**

Add to `backend/tests/test_jerseys.py`:

```python
def test_delete_wash_record(client):
    player = _create_player(client)
    wash_resp = client.post("/api/jerseys", json={"player_id": player["id"]})
    wash_id = wash_resp.json()["id"]

    response = client.delete(f"/api/jerseys/{wash_id}")
    assert response.status_code == 204


def test_delete_wash_record_not_found(client):
    response = client.delete("/api/jerseys/999")
    assert response.status_code == 404
```

**Step 2: Run the tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_jerseys.py::test_delete_wash_record -v
```

Expected: FAIL — 405 Method Not Allowed

**Step 3: Implement the DELETE endpoint**

Add to `backend/app/routers/jerseys.py`:

```python
@router.delete("/{wash_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wash_record(wash_id: int, db: Session = Depends(get_db)):
    wash = db.query(JerseyWash).filter(JerseyWash.id == wash_id).first()
    if not wash:
        raise HTTPException(status_code=404, detail="Wash record not found")
    db.delete(wash)
    db.commit()
```

**Step 4: Run the tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_jerseys.py::test_delete_wash_record tests/test_jerseys.py::test_delete_wash_record_not_found -v
```

Expected: Both PASS

**Step 5: Commit**

```bash
git add backend/tests/test_jerseys.py backend/app/routers/jerseys.py
git commit -m "feat: add DELETE /api/jerseys/{id} endpoint for undo"
```

---

## Task 6: TDD — Edge cases

**Files:**
- Modify: `backend/tests/test_jerseys.py`

**Step 1: Write edge case tests**

Add to `backend/tests/test_jerseys.py`:

```python
def test_undo_restores_previous_holder(client):
    alice = _create_player(client, name="Alice")
    bob = _create_player(client, name="Bob")

    client.post("/api/jerseys", json={"player_id": alice["id"]})
    bob_wash = client.post("/api/jerseys", json={"player_id": bob["id"]})
    bob_wash_id = bob_wash.json()["id"]

    # Bob is current holder
    current = client.get("/api/jerseys/current").json()
    assert current["player"]["name"] == "Bob"

    # Undo Bob's handoff
    client.delete(f"/api/jerseys/{bob_wash_id}")

    # Alice is now current holder again
    current = client.get("/api/jerseys/current").json()
    assert current["player"]["name"] == "Alice"


def test_multiple_handoffs_same_player(client):
    player = _create_player(client, name="Eager")

    client.post("/api/jerseys", json={"player_id": player["id"]})
    client.post("/api/jerseys", json={"player_id": player["id"]})
    client.post("/api/jerseys", json={"player_id": player["id"]})

    roster = client.get("/api/jerseys").json()["roster"]
    assert roster[0]["player"]["name"] == "Eager"
    assert roster[0]["wash_count"] == 3
```

**Step 2: Run all jersey tests**

```bash
cd backend && python -m pytest tests/test_jerseys.py -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add backend/tests/test_jerseys.py
git commit -m "test: add edge case tests for undo and multiple handoffs"
```

---

## Task 7: Run full test suite

**Step 1: Run all tests**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass (health + players CRUD + jerseys logic)

**Step 2: Commit any fixes if needed**

```bash
git add backend/
git commit -m "fix: resolve any issues from full test suite run"
```

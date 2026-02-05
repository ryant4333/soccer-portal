# Jersey Tracker Phase 1: Project Scaffolding & Docker

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up the full Docker Compose environment with SvelteKit frontend, FastAPI backend, and PostgreSQL database — all booting and talking to each other.

**Architecture:** Three Docker containers orchestrated with docker-compose. SvelteKit (adapter-node) serves the frontend on port 3000 and proxies /api requests to FastAPI on port 8000. FastAPI connects to PostgreSQL on port 5432 (internal only). Volume mounts enable hot reload for both frontend and backend during development.

**Tech Stack:** SvelteKit 2 (adapter-node, TypeScript), FastAPI (Python 3.12), PostgreSQL 16, Docker Compose, SQLAlchemy 2.0, Pydantic v2

**Prerequisite Plans:** None (this is the first phase)

---

## Task 1: Create directory structure

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `frontend/src/lib/.gitkeep`
- Create: `frontend/static/.gitkeep`
- Create: `db/.gitkeep`

**Step 1: Create all directories**

```bash
mkdir -p backend/app/routers
mkdir -p backend/tests
mkdir -p frontend/src/routes
mkdir -p frontend/src/lib
mkdir -p frontend/static
mkdir -p db
```

**Step 2: Create Python package init files**

Create empty files:
- `backend/app/__init__.py` (empty)
- `backend/app/routers/__init__.py` (empty)
- `backend/tests/__init__.py` (empty)

**Step 3: Commit**

```bash
git add backend/app/__init__.py backend/app/routers/__init__.py backend/tests/__init__.py
git commit -m "chore: create project directory structure"
```

---

## Task 2: Create database init script

**Files:**
- Create: `db/init.sql`

**Step 1: Write the init script**

```sql
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    nickname VARCHAR(255),
    usual_number VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jersey_washes (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    taken_at TIMESTAMP DEFAULT NOW()
);
```

**Step 2: Commit**

```bash
git add db/init.sql
git commit -m "feat: add database init script with players and jersey_washes tables"
```

---

## Task 3: Create backend requirements and Dockerfile

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`

**Step 1: Write requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
pydantic==2.10.4
httpx==0.28.1
pytest==8.3.4
```

**Step 2: Write Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Step 3: Commit**

```bash
git add backend/requirements.txt backend/Dockerfile
git commit -m "chore: add backend Dockerfile and Python dependencies"
```

---

## Task 4: Create minimal FastAPI app with health endpoint

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/schemas.py`

**Step 1: Write database.py**

```python
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2: Write models.py**

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    nickname = Column(String(255), nullable=True)
    usual_number = Column(String(10), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class JerseyWash(Base):
    __tablename__ = "jersey_washes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    taken_at = Column(DateTime, server_default=func.now())
```

**Step 3: Write schemas.py**

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlayerCreate(BaseModel):
    name: str
    nickname: Optional[str] = None
    usual_number: Optional[str] = None


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    usual_number: Optional[str] = None


class PlayerResponse(BaseModel):
    id: int
    name: str
    nickname: Optional[str]
    usual_number: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class JerseyWashCreate(BaseModel):
    player_id: int


class JerseyWashResponse(BaseModel):
    id: int
    player_id: int
    taken_at: datetime

    model_config = {"from_attributes": True}


class CurrentHolder(BaseModel):
    player: PlayerResponse
    taken_at: datetime


class JerseyRosterEntry(BaseModel):
    player: PlayerResponse
    wash_count: int
```

**Step 4: Write main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Jersey Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

**Step 5: Commit**

```bash
git add backend/app/main.py backend/app/database.py backend/app/models.py backend/app/schemas.py
git commit -m "feat: add FastAPI app with database models, schemas, and health endpoint"
```

---

## Task 5: Create backend test infrastructure

**Files:**
- Create: `backend/tests/conftest.py`

**Step 1: Write conftest.py**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**Step 2: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "test: add pytest fixtures with SQLite test database"
```

---

## Task 6: Write and run health endpoint test

**Files:**
- Create: `backend/tests/test_health.py`

**Step 1: Write the test**

```python
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run the test to verify it passes**

```bash
cd backend && python -m pytest tests/test_health.py -v
```

Expected output:
```
tests/test_health.py::test_health_check PASSED
```

**Step 3: Commit**

```bash
git add backend/tests/test_health.py
git commit -m "test: add health endpoint test"
```

---

## Task 7: Create SvelteKit project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/svelte.config.js`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/app.html`
- Create: `frontend/src/app.d.ts`
- Create: `frontend/src/routes/+page.svelte`
- Create: `frontend/src/routes/+layout.svelte`

**Step 1: Write package.json**

```json
{
  "name": "jersey-tracker-frontend",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "vite dev --host",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@sveltejs/adapter-node": "^5.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^4.0.0",
    "svelte": "^5.0.0",
    "svelte-check": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^6.0.0"
  }
}
```

**Step 2: Write svelte.config.js**

```javascript
import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter()
	}
};

export default config;
```

**Step 3: Write vite.config.ts**

```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: 'http://backend:8000',
				changeOrigin: true
			}
		}
	}
});
```

**Step 4: Write tsconfig.json**

```json
{
  "extends": "./.svelte-kit/tsconfig.json",
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "strict": true,
    "moduleResolution": "bundler"
  }
}
```

**Step 5: Write src/app.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Jersey Tracker</title>
    %sveltekit.head%
  </head>
  <body data-sveltekit-prerender="false">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

**Step 6: Write src/app.d.ts**

```typescript
/// <reference types="@sveltejs/kit" />

declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface Platform {}
  }
}

export {};
```

**Step 7: Write src/routes/+layout.svelte**

```svelte
<slot />
```

**Step 8: Write src/routes/+page.svelte**

```svelte
<h1>Jersey Tracker</h1>
<p>Coming soon...</p>
```

**Step 9: Commit**

```bash
git add frontend/package.json frontend/svelte.config.js frontend/vite.config.ts frontend/tsconfig.json frontend/src/app.html frontend/src/app.d.ts frontend/src/routes/+page.svelte frontend/src/routes/+layout.svelte
git commit -m "feat: add SvelteKit project skeleton"
```

---

## Task 8: Create frontend Dockerfile

**Files:**
- Create: `frontend/Dockerfile`

**Step 1: Write Dockerfile**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
```

**Step 2: Commit**

```bash
git add frontend/Dockerfile
git commit -m "chore: add frontend Dockerfile"
```

---

## Task 9: Create docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

**Step 1: Write docker-compose.yml**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: jersey
      POSTGRES_PASSWORD: jersey
      POSTGRES_DB: jersey_tracker
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jersey -d jersey_tracker"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://jersey:jersey@db:5432/jersey_tracker
    volumes:
      - ./backend/app:/app/app
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
    depends_on:
      - backend

volumes:
  pgdata:
```

**Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose with frontend, backend, and database services"
```

---

## Task 10: Verify full stack boots

**Step 1: Build and start all services**

```bash
docker compose up --build
```

Expected: All three services start without errors.

**Step 2: Test backend health endpoint**

```bash
curl http://localhost:8000/api/health
```

Expected output:
```json
{"status":"ok"}
```

**Step 3: Test frontend loads**

Open http://localhost:3000 in browser. Expected: Page shows "Jersey Tracker" heading and "Coming soon..." text.

**Step 4: Stop services**

```bash
docker compose down
```

**Step 5: Commit any fixes if needed**

```bash
git add -A
git commit -m "fix: resolve any boot issues from integration testing"
```

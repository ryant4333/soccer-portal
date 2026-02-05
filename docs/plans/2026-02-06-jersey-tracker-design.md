# Jersey Tracker — Design Document

## Overview

A PWA to help manage a soccer team's jersey washing rotation. The team manager and players use it to track who currently has the jerseys and whose turn is next based on fewest washes.

## Architecture

Three containers in a single `docker-compose.yml`:

| Container | Tech | Role |
|---|---|---|
| `frontend` | SvelteKit (adapter-node) | PWA served as SSR/static, proxies API calls |
| `backend` | FastAPI (Python) | REST API, business logic |
| `db` | PostgreSQL 16 | Data persistence |

**Request flow:** Browser → SvelteKit container (:3000) → FastAPI container (:8000) → Postgres (:5432)

SvelteKit handles the PWA manifest, service worker, and all UI. It calls the FastAPI backend for data. FastAPI owns the database connection and all business logic. Postgres is internal only — not exposed outside Docker.

**Development workflow:** `docker compose up` starts everything. Hot reload enabled for both SvelteKit and FastAPI via volume mounts.

## Database

### `players`

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | Auto-increment |
| `name` | `VARCHAR(255) NOT NULL` | Player full name |
| `nickname` | `VARCHAR(255)` | Optional nickname |
| `usual_number` | `VARCHAR(10)` | Their usual jersey number |
| `created_at` | `TIMESTAMP DEFAULT NOW()` | When they were added |

### `jersey_washes`

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | Auto-increment |
| `player_id` | `INTEGER REFERENCES players(id)` | Who took the jerseys |
| `taken_at` | `TIMESTAMP DEFAULT NOW()` | Date they took possession |

**Key queries:**
- **Current holder:** Most recent row in `jersey_washes` (latest `taken_at`)
- **Wash count per player:** `COUNT(*) FROM jersey_washes WHERE player_id = X`
- **Player list sorted by fewest washes:** `LEFT JOIN` players to jersey_washes, `GROUP BY` player, `ORDER BY` count ascending
- **New handoff:** `INSERT` a row into `jersey_washes` — append-only
- **Undo accidental handoff:** `DELETE` the wash record by id; previous holder becomes current automatically

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/players` | All players (id, name, nickname, usual_number) |
| `POST` | `/api/players` | Add a new player (name, nickname, usual_number) |
| `PUT` | `/api/players/{id}` | Update player details |
| `DELETE` | `/api/players/{id}` | Remove a player |
| `GET` | `/api/jerseys` | Current holder + all players with wash counts, sorted by fewest washes ascending |
| `POST` | `/api/jerseys` | Record a new handoff (player_id) |
| `GET` | `/api/jerseys/current` | Who currently has the jerseys + date taken |
| `DELETE` | `/api/jerseys/{id}` | Delete a wash record (undo accidental handoff) |

## UI

### Jersey Tracker Page (main view)

**Top panel — Current Holder:**
- Large card showing: player name (nickname if set), usual number, and the date they took the jerseys
- If no one has them yet, shows "No one has the jerseys"

**Below — Wash Roster:**
- List of all players sorted by fewest washes first (person who should go next is at the top)
- Each row shows: name/nickname, usual number, wash count
- Each row has an "I've got them" button
- Tapping the button calls `POST /api/jerseys` with the player's id and refreshes the view
- The previous holder moves into the list with their count incremented

### No auth
Anyone with the link can use it. No login or user accounts.

## Tech Details

### PWA
- SvelteKit with `@vite-pwa/sveltekit` or manual service worker
- Manifest with app name, icons, theme color
- Installable on mobile home screens

### Docker Compose
- `frontend`: Node-based SvelteKit container, port 3000
- `backend`: Python FastAPI container with uvicorn, port 8000
- `db`: PostgreSQL 16, port 5432 (internal only)
- Volume mounts for hot reload in development
- Named volume for Postgres data persistence

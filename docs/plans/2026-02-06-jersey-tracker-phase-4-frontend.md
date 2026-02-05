# Jersey Tracker Phase 4: Frontend Core UI

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the SvelteKit frontend with Current Holder card and Wash Roster list, fully wired to the backend API

**Architecture:** SvelteKit with adapter-node and TypeScript. API calls go through a thin client module. The main page loads jersey data on mount and refreshes after each action. Vite dev server proxies /api requests to the FastAPI backend.

**Tech Stack:** SvelteKit 2, Svelte 5, TypeScript, adapter-node, Vite

**Prerequisite Plans:** Phases 1-3 must be complete (backend fully functional)

---

## Task 1: Create TypeScript types

**Files:**
- Create: `frontend/src/lib/types.ts`

**Step 1: Write the type definitions**

Create `frontend/src/lib/types.ts`:

```typescript
export interface Player {
  id: number;
  name: string;
  nickname: string | null;
  usual_number: string | null;
  created_at: string;
}

export interface CurrentHolder {
  player: Player;
  taken_at: string;
}

export interface JerseyRosterEntry {
  player: Player;
  wash_count: number;
}

export interface JerseyData {
  current_holder: CurrentHolder | null;
  roster: JerseyRosterEntry[];
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/types.ts
git commit -m "feat: add TypeScript interfaces for jersey tracker data"
```

---

## Task 2: Create API client module

**Files:**
- Create: `frontend/src/lib/api.ts`

**Step 1: Write the API client**

Create `frontend/src/lib/api.ts`:

```typescript
import type { JerseyData } from './types';

export async function fetchJerseyData(): Promise<JerseyData> {
  const response = await fetch('/api/jerseys');
  if (!response.ok) {
    throw new Error(`Failed to fetch jersey data: ${response.status}`);
  }
  return response.json();
}

export async function recordHandoff(playerId: number): Promise<void> {
  const response = await fetch('/api/jerseys', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_id: playerId }),
  });
  if (!response.ok) {
    throw new Error(`Failed to record handoff: ${response.status}`);
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add API client module for jersey data"
```

---

## Task 3: Create CurrentHolder component

**Files:**
- Create: `frontend/src/lib/components/CurrentHolder.svelte`

**Step 1: Write the component**

Create `frontend/src/lib/components/CurrentHolder.svelte`:

```svelte
<script lang="ts">
  import type { CurrentHolder } from '$lib/types';

  interface Props {
    currentHolder: CurrentHolder | null;
  }

  let { currentHolder }: Props = $props();

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-AU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  function displayName(player: { name: string; nickname: string | null }): string {
    return player.nickname || player.name;
  }
</script>

<section class="current-holder">
  <h2>Current Holder</h2>
  {#if currentHolder}
    <div class="holder-card">
      <span class="holder-name">{displayName(currentHolder.player)}</span>
      {#if currentHolder.player.usual_number}
        <span class="holder-number">#{currentHolder.player.usual_number}</span>
      {/if}
      <span class="holder-date">Since {formatDate(currentHolder.taken_at)}</span>
    </div>
  {:else}
    <div class="holder-card empty">
      <span class="holder-name">No one has the jerseys</span>
    </div>
  {/if}
</section>

<style>
  .current-holder {
    margin-bottom: 2rem;
  }

  h2 {
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
    margin-bottom: 0.75rem;
  }

  .holder-card {
    background: #1a7a3a;
    color: white;
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .holder-card.empty {
    background: #888;
  }

  .holder-name {
    font-size: 1.5rem;
    font-weight: 700;
  }

  .holder-number {
    font-size: 1.1rem;
    opacity: 0.85;
  }

  .holder-date {
    font-size: 0.875rem;
    opacity: 0.7;
    margin-top: 0.25rem;
  }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/lib/components/CurrentHolder.svelte
git commit -m "feat: add CurrentHolder component"
```

---

## Task 4: Create WashRoster component

**Files:**
- Create: `frontend/src/lib/components/WashRoster.svelte`

**Step 1: Write the component**

Create `frontend/src/lib/components/WashRoster.svelte`:

```svelte
<script lang="ts">
  import type { JerseyRosterEntry } from '$lib/types';

  interface Props {
    roster: JerseyRosterEntry[];
    onHandoff: (playerId: number) => void;
  }

  let { roster, onHandoff }: Props = $props();

  function displayName(player: { name: string; nickname: string | null }): string {
    return player.nickname || player.name;
  }
</script>

<section class="wash-roster">
  <h2>Wash Roster</h2>
  {#if roster.length === 0}
    <p class="empty-message">No players added yet.</p>
  {:else}
    <ul class="roster-list">
      {#each roster as entry, i (entry.player.id)}
        <li class="roster-item" class:next-up={i === 0}>
          <div class="player-info">
            <span class="player-name">{displayName(entry.player)}</span>
            <span class="player-details">
              {#if entry.player.usual_number}
                #{entry.player.usual_number} &middot;
              {/if}
              {entry.wash_count} {entry.wash_count === 1 ? 'wash' : 'washes'}
            </span>
          </div>
          <button class="handoff-btn" onclick={() => onHandoff(entry.player.id)}>
            I've got them
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .wash-roster {
    margin-bottom: 2rem;
  }

  h2 {
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #666;
    margin-bottom: 0.75rem;
  }

  .empty-message {
    color: #999;
    font-style: italic;
  }

  .roster-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .roster-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f8f8f8;
    border-radius: 8px;
    padding: 1rem;
    border: 2px solid transparent;
  }

  .roster-item.next-up {
    border-color: #1a7a3a;
    background: #f0faf3;
  }

  .player-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .player-name {
    font-weight: 600;
    font-size: 1rem;
  }

  .player-details {
    font-size: 0.8rem;
    color: #666;
  }

  .handoff-btn {
    background: #1a7a3a;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .handoff-btn:hover {
    background: #15632f;
  }

  .handoff-btn:active {
    background: #0f4d24;
  }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/lib/components/WashRoster.svelte
git commit -m "feat: add WashRoster component with handoff buttons"
```

---

## Task 5: Wire up the main page

**Files:**
- Modify: `frontend/src/routes/+page.svelte`

**Step 1: Update the main page**

Replace `frontend/src/routes/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchJerseyData, recordHandoff } from '$lib/api';
  import type { JerseyData } from '$lib/types';
  import CurrentHolder from '$lib/components/CurrentHolder.svelte';
  import WashRoster from '$lib/components/WashRoster.svelte';

  let data: JerseyData | null = $state(null);
  let loading = $state(true);
  let error: string | null = $state(null);

  async function loadData() {
    try {
      error = null;
      data = await fetchJerseyData();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load data';
    } finally {
      loading = false;
    }
  }

  async function handleHandoff(playerId: number) {
    try {
      error = null;
      await recordHandoff(playerId);
      await loadData();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to record handoff';
    }
  }

  onMount(loadData);
</script>

{#if loading}
  <p class="status-message">Loading...</p>
{:else if error}
  <p class="status-message error">{error}</p>
{:else if data}
  <CurrentHolder currentHolder={data.current_holder} />
  <WashRoster roster={data.roster} onHandoff={handleHandoff} />
{/if}

<style>
  .status-message {
    text-align: center;
    padding: 2rem;
    color: #666;
  }

  .status-message.error {
    color: #c0392b;
  }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat: wire up main page with data fetching and handoff actions"
```

---

## Task 6: Create global layout with styles

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`

**Step 1: Update the layout**

Replace `frontend/src/routes/+layout.svelte`:

```svelte
<header>
  <h1>Jersey Tracker</h1>
</header>

<main>
  <slot />
</main>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, sans-serif;
    background: #f5f5f5;
    color: #333;
    min-height: 100vh;
  }

  header {
    background: #1a7a3a;
    color: white;
    padding: 1rem;
    text-align: center;
  }

  header h1 {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }

  main {
    max-width: 480px;
    margin: 0 auto;
    padding: 1.5rem 1rem;
  }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/routes/+layout.svelte
git commit -m "feat: add global layout with header and mobile-first styles"
```

---

## Task 7: Verify end-to-end with Docker

**Step 1: Build and start all services**

```bash
docker compose up --build
```

**Step 2: Add test players via API**

```bash
curl -X POST http://localhost:8000/api/players -H "Content-Type: application/json" -d '{"name": "Alice", "nickname": "Ali", "usual_number": "7"}'
curl -X POST http://localhost:8000/api/players -H "Content-Type: application/json" -d '{"name": "Bob", "usual_number": "9"}'
curl -X POST http://localhost:8000/api/players -H "Content-Type: application/json" -d '{"name": "Charlie", "nickname": "Chuck", "usual_number": "3"}'
```

**Step 3: Manually verify in browser**

Open http://localhost:3000 and verify:
- "No one has the jerseys" card is shown
- All 3 players appear in the wash roster with 0 washes
- Click "I've got them" on Alice — she becomes current holder
- Click "I've got them" on Bob — he becomes current holder, Alice's count goes to 1
- Roster re-sorts after each action

**Step 4: Stop services**

```bash
docker compose down
```

**Step 5: Commit any fixes**

```bash
git add frontend/
git commit -m "fix: resolve any issues from end-to-end testing"
```

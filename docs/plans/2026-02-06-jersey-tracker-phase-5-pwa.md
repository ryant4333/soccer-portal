# Jersey Tracker Phase 5: PWA & Polish

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the Jersey Tracker installable as a PWA on mobile devices with offline shell caching, proper manifest, and app icons

**Architecture:** Add a web app manifest and service worker to the existing SvelteKit frontend. SvelteKit's built-in service worker support is used to cache the app shell for offline access. The manifest enables "Add to Home Screen" on mobile.

**Tech Stack:** SvelteKit 2, SvelteKit built-in service worker, Web App Manifest

**Prerequisite Plans:** Phases 1-4 must be complete (full app functional)

---

## Task 1: Create app icons

**Files:**
- Create: `frontend/static/icon-192x192.svg`
- Create: `frontend/static/icon-512x512.svg`
- Create: `frontend/static/favicon.svg`

**Step 1: Create the SVG icon**

Create `frontend/static/favicon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="64" fill="#1a7a3a"/>
  <text x="256" y="340" font-family="Arial, sans-serif" font-size="280" font-weight="bold" fill="white" text-anchor="middle">JT</text>
</svg>
```

Copy the same file as the icon sizes (SVGs are resolution-independent):

Create `frontend/static/icon-192x192.svg` — same content as favicon.svg

Create `frontend/static/icon-512x512.svg` — same content as favicon.svg

**Step 2: Commit**

```bash
git add frontend/static/favicon.svg frontend/static/icon-192x192.svg frontend/static/icon-512x512.svg
git commit -m "feat: add SVG app icons"
```

---

## Task 2: Create web app manifest

**Files:**
- Create: `frontend/static/manifest.json`
- Modify: `frontend/src/app.html`

**Step 1: Write manifest.json**

Create `frontend/static/manifest.json`:

```json
{
  "name": "Jersey Tracker",
  "short_name": "Jerseys",
  "description": "Track your team's jersey washing rotation",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f5f5f5",
  "theme_color": "#1a7a3a",
  "icons": [
    {
      "src": "/icon-192x192.svg",
      "sizes": "192x192",
      "type": "image/svg+xml"
    },
    {
      "src": "/icon-512x512.svg",
      "sizes": "512x512",
      "type": "image/svg+xml"
    }
  ]
}
```

**Step 2: Update app.html with manifest and meta tags**

Update `frontend/src/app.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#1a7a3a" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <link rel="manifest" href="/manifest.json" />
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="apple-touch-icon" href="/icon-192x192.svg" />
    <title>Jersey Tracker</title>
    %sveltekit.head%
  </head>
  <body data-sveltekit-prerender="false">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

**Step 3: Commit**

```bash
git add frontend/static/manifest.json frontend/src/app.html
git commit -m "feat: add web app manifest and PWA meta tags"
```

---

## Task 3: Create service worker

**Files:**
- Create: `frontend/src/service-worker.ts`

SvelteKit has built-in service worker support. Any file at `src/service-worker.ts` is automatically registered.

**Step 1: Write the service worker**

Create `frontend/src/service-worker.ts`:

```typescript
/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

const CACHE_NAME = `jersey-tracker-${version}`;
const ASSETS = [...build, ...files];

// Install: cache app shell
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

// Activate: clean old caches
self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
});

// Fetch: serve app shell from cache, API requests always go to network
self.addEventListener('fetch', (event: FetchEvent) => {
  const url = new URL(event.request.url);

  // Skip API requests — always fetch fresh data
  if (url.pathname.startsWith('/api')) {
    return;
  }

  // For app shell: try cache first, fall back to network
  if (event.request.method === 'GET') {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return cached || fetch(event.request);
      })
    );
  }
});
```

**Step 2: Commit**

```bash
git add frontend/src/service-worker.ts
git commit -m "feat: add service worker with app shell caching"
```

---

## Task 4: Verify PWA functionality

**Step 1: Build the frontend**

```bash
cd frontend && npm run build
```

Expected: Build succeeds without errors, service worker is generated.

**Step 2: Start full stack with Docker**

```bash
docker compose up --build
```

**Step 3: Verify in Chrome DevTools**

Open http://localhost:3000 in Chrome and check:

1. **Application → Manifest**: Manifest is detected, shows "Jersey Tracker", icons load
2. **Application → Service Workers**: Service worker is registered and active
3. **Lighthouse → PWA**: Run a PWA audit — should pass basic installability checks

**Step 4: Test install prompt**

On Chrome desktop: look for install icon in the address bar, or on mobile: "Add to Home Screen" should appear.

**Step 5: Stop services**

```bash
docker compose down
```

**Step 6: Commit any fixes**

```bash
git add frontend/
git commit -m "fix: resolve any PWA issues from testing"
```

---

## Task 5: Final smoke test

**Step 1: Clean build and boot**

```bash
docker compose down -v
docker compose up --build
```

**Step 2: Full user flow test**

1. Open http://localhost:3000
2. Add players via curl:
   ```bash
   curl -X POST http://localhost:8000/api/players -H "Content-Type: application/json" -d '{"name": "Alice", "usual_number": "7"}'
   curl -X POST http://localhost:8000/api/players -H "Content-Type: application/json" -d '{"name": "Bob", "usual_number": "9"}'
   ```
3. Refresh the page — both players appear with 0 washes
4. Click "I've got them" on Alice — she becomes current holder
5. Click "I've got them" on Bob — he becomes current holder, roster re-sorts
6. Verify PWA installs correctly on mobile or via Chrome install prompt

**Step 3: Stop services**

```bash
docker compose down
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete Jersey Tracker PWA"
```

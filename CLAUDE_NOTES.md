# Claude notes — issue #15 (train detail page)

## Assumptions
- Added `GET /trains/{id}` returning 404 when the train doesn't exist. The existing endpoints had no pydantic models or framework conventions to mirror, so I matched the inline-dict style already used by `GET /trains`.
- Used **hash-based routing** (`#/trains/{id}`) in the frontend rather than adding `react-router-dom`. Reasons:
  - Keeps the dependency footprint minimal and works with the static `serve dist` start command (no SPA fallback needed).
  - Existing code was a single-file React app; hash routing was a low-risk drop-in.
- Train name in the list is a real `<a href="#/trains/{id}">` (for middle-click/copy-link), and the whole row is also clickable as a UX nicety.
- Moved the **+ Add Train** button out of the global header and into a list-only toolbar, since it doesn't apply on the detail page.
- Did not run the frontend or backend (no Postgres / Node toolchain expected in this autonomous environment). Backend was syntax-checked with `ast.parse`.

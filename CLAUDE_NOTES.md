# Notes for issue #13 (Train detail page)

## Assumptions

- **No CLAUDE.md exists in the repo.** Followed the conventions visible in the existing code (single `App.jsx`, FastAPI route style in `backend/main.py`, README format).
- **Detail page lives at `/trains/:id`** — added `react-router-dom@^6.26.0` as a frontend dependency. The previous app had no router; a real "detail page" needs a real URL, and React Router is the standard choice. This requires the frontend host (Railway `serve`) to fall back to `index.html` for client-side routes; `serve` does this by default, so no extra config was added.
- **Backend endpoint shape:** `GET /trains/{train_id}` returns the same flat JSON object shape that `GET /trains` items use. 404 (via `HTTPException`) when the id does not exist. No PATCH/DELETE — issue only asked for a detail page + API.
- **Train name in the list is the clickable link** to the detail page (rather than making the whole row clickable). Less surprising for keyboard/screen-reader users.
- **Detail page UI** shows the same five fields as the list (name, route, description, color, top_speed) in a `<dl>`, plus a thin color bar at the top of the card. Back arrow in the header returns to `/`. Dark-mode state is lifted to the router root and passed to both pages.
- **No tests were added** — the project has no existing test suite or framework configured.
- **UI was not manually verified in a browser** (no browser available in this environment). Verified: backend route registration via FastAPI introspection; frontend `npm run build` succeeds with the new router code.

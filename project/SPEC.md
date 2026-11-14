## SPEC: Interview Reflections Dashboard
## 1. Purpose & Scope
- A single-user browser dashboard where a college student records reflections on coding interview problems (LeetCode, HackerRank, NeetCode, etc.) and views an AI-structured learning summary for each one.
- Sprint 1 built the UI layer. Sprint 2 adds a Python/Flask backend so reflections persist across page refreshes and server restarts. Everything still runs on localhost, now served from http://localhost:5000.
- Initial state MUST load from the backend (GET /api/entries), not from a file in the frontend. The starting data comes from backend/seed_data.json (the Sprint 1 mock_data.json, moved). Adds, edits, and deletes MUST persist on the server and survive a page refresh and a server restart.
- Work happens in two phases. Phase 1 stores entries in a JSON file (backend/data.json). Phase 2 replaces that file with a SQLite database. The final submission MUST use SQLite. Only the storage-layer functions change between phases. Routes, validation, and frontend code MUST NOT change in Phase 2.
- Flask serves the files in ./frontend and the /api routes from the same origin. No CORS configuration is needed, and the frontend MUST use relative URLs such as /api/entries.
- "Send to AI" MUST use a canned response built by the backend (build_canned_review) after a short delay in the UI. No real LLM call is made in Sprint 2. 
- Non-Goals: no login or multiple users; no real LLM or external API calls; no hosting, running, or judging code; no study plans, leaderboards, or social features; no ORM; no endpoints beyond Section 3; no pagination, search, or filtering; no deployment; no packages beyond Flask
## 2. Invariants & Negative Constraints
Frontend 
- The frontend MUST consist of ./frontend/index.html, ./frontend/style.css, and ./frontend/app.js. ./frontend/mock_data.json MUST NOT exist after Sprint 2.
- All styling MUST reside in ./style.css (no inline style="..." attributes). Inline event handlers (onclick= etc.) MUST NOT be used; all listeners are attached in app.js.
- The page MUST NOT load external CSS frameworks, fonts, scripts, or CDNs. JavaScript MUST be vanilla.fetch() calls go only to the app's own relative /api paths.
- style.css MUST begin with the universal reset: *, *::before, *::after { box-sizing: border-box; }.
- Colors MUST be defined once as custom properties on :root. The palette MUST use one accent color.
- Spacing and font sizes MUST use rem. px MAY be used only for borders.
- Styling MUST use class selectors. ID selectors MUST NOT be used for styling. IDs MAY be used for label/for pairing.
- The layout MUST show the form and the entry list side by side (CSS Grid) at 768px and wider, and collapse into a single vertical column below 768px, with the form first.
- App state MUST be a single entries array in app.js. renderEntries() MUST rebuild the list from that array. No other code may create or remove cards directly.
- Edit, delete, and Send to AI MUST be handled by event delegation on the list container, using data-action attributes on the buttons.
- User-entered text MUST be inserted with textContent (or equivalent), never innerHTML.
- Loading MUST live in one function, loadEntries(), and the AI request MUST live in one function, requestAiReview(entry), which returns a Promise. In Sprint 2 these two functions, plus the submit and delete handlers, are the only places that call the backend.
- localStorage, sessionStorage, and cookies MUST NOT be used.
- app.js MUST NOT contain hardcoded entry arrays or reference mock_data.json.
- The entries array MUST NOT be changed for an add, edit, delete, or review until the server confirms the change. The frontend MUST NOT generate ids.
- All fetch() calls MUST check the response status and be wrapped so nothing throws an uncaught error. alert() MUST NOT be used for errors.
- backend/seed_data.json MUST contain at least 5 entries using exactly these fields: id, problem_name, source, topic, difficulty, result, time_minutes, approach, struggles, ai_review, created_at.
- In seed_data.json, at least 2 entries MUST have an ai_review object, at least 2 MUST have ai_review: null, at least 1 MUST have an empty approach, and the entries MUST include all three results (Solved, Partial, Failed).
- An ai_review object MUST have exactly four string fields: key_concept, knowledge_gap, takeaway, area_for_review.
Backend: Repo Layout
- The repo MUST contain /backend (app.py, schema.sql, seed.py, seed_data.json, requirements.txt), /frontend (index.html, style.css, app.js), .gitignore, SPEC.md, SPRINT1.md, and SPRINT2.md.
- requirements.txt MUST list Flask and nothing else. It MUST be UTF-8 encoded. .gitignore MUST ignore pycache/, .pytest_cache/,venv/, .venv/, .env, *.db, and backend/data.json.
- venv/, pycache/, and the database file MUST NOT be committed.
Backend: Structure 
- backend/app.py is the single Flask entry point. It MUST run with host="localhost", port=5000, and MUST NOT use debug=True.
- Only the Python standard library and Flask may be imported. Phase 2 uses the built-in sqlite3 module with raw SQL.
- Route handlers MUST NOT read files or run SQL directly. They MUST call only these storage functions: get_all_entries(), get_entry(entry_id), create_entry(data), update_entry(entry_id, data), delete_entry(entry_id), save_review(entry_id, review).
- Validation MUST live in one function, validate_entry(payload), that returns (cleaned, errors). The canned review MUST live in one function, build_canned_review(entry).
- Each route MUST be a separate function using method decorators (@app.get, @app.post, @app.put, @app.delete) on /api/... paths built from the resource noun "entries".
Backend: Data structures and types 
- An entry is a Python dict. In Phase 1 the collection is a list of dicts loaded with json.load() and written with json.dump().
- Entry fields are exactly: id, problem_name, source, topic, difficulty, result, time_minutes, approach, struggles, ai_review, created_at.
- id and time_minutes MUST be int. All text fields MUST be str with surrounding whitespace stripped. topic, approach, and struggles default to "" when missing. ai_review is a dict with exactly four string fields or None. created_at is a UTC ISO 8601 string such as 2026-10-12T09:15:00Z.
- Payload values MUST be read with .get() or a guarded lookup. A missing key MUST NOT raise KeyError.
- The server sets id, created_at, and ai_review. Any id, created_at, or ai_review in a POST or PUT body MUST be ignored.
- PUT replaces only the eight editable fields (problem_name, source, topic, difficulty, result, time_minutes, approach, struggles). It MUST NOT change id, created_at, or ai_review.
Backend: Validation
- The request body MUST be read with request.get_json(silent=True). If the result is not a dict, respond 400.
- Required: problem_name (non-empty, at most 100 characters), source (LeetCode, HackerRank, NeetCode, or Other), difficulty (Easy, Medium, or Hard), result (Solved, Partial, or Failed), time_minutes.
- time_minutes MUST be a JSON integer from 1 to 600. Booleans, floats, strings, and null MUST be rejected.
- Optional text fields MUST be strings if present. A non-string value is a 400.
- All field errors are collected and returned together, not just the first.
Backend: Status codes and errors 
- Every route MUST return one of 200, 201, 204, 400, or 404 explicitly. Unhandled exceptions MUST return 500.
- Error bodies are JSON: {"error": "message"}. Validation failures add "fields": {"field_name": "message"}.
- A global error handler MUST return JSON for every error, keep the status code of Flask HTTP exceptions, and return {"error": "Internal server error."} with 500 for anything else. Stack traces MUST NOT appear in responses.
Backend: Peristence 
- New entry ids MUST be max(existing ids) + 1 (or 1 if the list is empty) in Phase 1. data.json is created from seed_data.json if missing.
- Phase 2 uses a table "entries" with id INTEGER PRIMARY KEY AUTOINCREMENT. This supersedes max + 1, and ids are never reused after a delete.
- The Phase 2 schema MUST live in backend/schema.sql and run with CREATE TABLE IF NOT EXISTS. ai_review is stored as JSON text (NULL when absent) and converted to and from a dict in the storage layer.
- Phase 2 SQL MUST use ? placeholders. Building SQL with f-strings or string concatenation MUST NOT happen.
- Phase 2 connections MUST be closed after each operation, and writes MUST be committed.
- Phase 2 seed.py MUST keep the seed ids, MUST do nothing if the table already has rows, and MUST NOT be run automatically by app.py.
- Records MUST survive stopping the server with Ctrl+C and restarting it.
## 3. UI Content & Interface Contract
- The page MUST use semantic landmarks: one `<header>`, one `<main>`, one `<footer>`, and each content group inside its own `<section>` with a heading.
- There MUST be exactly one `<h1>`, and heading levels MUST NOT skip (h1 then h2 then h3).
- Header: `<h1>` "Interview Reflections", a one-line subtitle, and a stats row with three values: Total entries, Solve rate, Average time (minutes).
- Solve rate = Solved entries / total entries, rounded to a whole percent. Partial does not count as solved.
- Stats MUST update on every add, edit, and delete.
- With zero entries, Solve rate and Average time MUST display "—", never NaN or 0%.
- Form section (`<h2>` "New reflection"), with a visible `<label>` on every field:  
- Required: problem name (text, max 100 characters), source (select: LeetCode, HackerRank, NeetCode, Other), difficulty (select: Easy, Medium, Hard), result (select: Solved, Partial, Failed), time in minutes (number).
- Optional: topic (text), approach (textarea), struggles (textarea).
- Time MUST be a whole number from 1 to 600.
- The form MUST NOT submit if a required field is empty or time is outside 1 to 600. Each error MUST appear as visible text next to its field, and MUST clear as soon as the user edits that field. alert() MUST NOT be used for validation. Client-side validation runs first and shows all errors at once. The server validates again.
If the server returns 400, nothing is added or changed. Each message in the response's "fields" map MUST appear as visible text next to its field and clear when the user edits that field. Any other error appears in a form-level message element (`<p class="field-error" id="form-error" aria-live="polite">`) placed above the form buttons.
- The form root MUST carry data-mode="add" or data-mode="edit". In edit mode the submit button reads "Save changes" and a "Cancel" button appears; in add mode the submit button reads "Add entry".
- A successful add (201) or save (200) MUST reset the form to add mode and clear all fields, including the form-level message. 
- Entry list section (`<h2>` "Your entries"), with a count such as "5 entries".
- Each entry MUST be an `<article class="card">` inside a container that uses display: grid or display: flex with gap.
- Each card MUST carry data-id, data-result, data-difficulty, and data-ai-state (none, loading, or done) attributes, and CSS MUST style from them.
- Each card MUST show: problem name (`<h3>`), source, topic (if any), time, created date, a result badge, a difficulty badge, approach text, and struggles text (each only if non-empty).
- Badges MUST contain text (Solved, Medium, etc.), not color alone, and MUST differ visually per value.
- Each card MUST have Edit, Delete, and Send to AI buttons.
- An empty list MUST show: "No entries yet. Add your first reflection using the form."
- Edit: clicking Edit MUST fill the form with that entry's values and switch the form to edit mode. Saving MUST update the card in place without changing its position or id. Cancel MUST return the form to add mode with no changes.
- Delete: MUST ask for confirmation first (window.confirm() is acceptable). Cancelling MUST keep the entry. Confirming MUST remove the card and update the stats. If the entry being edited is deleted, the form MUST return to add mode.
- Two separate scroll bars for form section and list of submitted problems 
- Send to AI:
- The button MUST have the HTML disabled attribute when the entry's approach is empty or only whitespace, with a visible hint: "Add approach text to enable AI review." The backend enforces the same rule and returns 400 for such an entry.
- On click, the button MUST become disabled and read "Analyzing…", and the card's data-ai-state MUST be loading for about 1.5 seconds. The request is POST/api/entries/`<id>`/review.requestAiReview keeps a minimum 1.5 second loading time even if the server answers sooner. A second click during loading MUST NOT start a second request.
- When the Promise resolves, the entry in the entries array MUST be replaced with the entry returned by the server (its ai_review is set), the card MUST show the summary, and the button MUST read "Re-run review". If the request fails, a form-level message appears and the button returns to its previous state.
- AI summary panel on a card MUST show four labeled fields: Key concept, Knowledge gap, Takeaway, Area for review.
- A card with no summary MUST show: "No AI review yet. Send this entry to get a structured summary."
- Every button MUST have four visually distinct states in style.css: :hover, :focus-visible, :active, and :disabled.Disabled buttons MUST NOT look clickable and MUST NOT react to hover.
- If the request to load entries fails, the list MUST show: "Couldn't load entries. Check that the Flask server is running." Nothing may throw an uncaught error.
API Contract
- Method: GET -- Path: /api/entries -- Request body: none -- Success: 200, list of entries ordered by id -- Errors: 500 
- Method: GET -- Path: /api/entries/`<id>` -- Request body: none -- Success: 200, one entry -- Errors: 404 
- Method: POST -- Path: /api/entries -- Request body: the eight editable fields -- Success: 201, the new entry with id -- Errors: 400 
- Method: PUT -- Path: /api/entries/`<id>` -- Request body: the eight editable fields -- Success: 200, the updated entry -- Errors: 400, 404 
- Method: DELETE -- Path: /api/entries/`<id>` -- Request Body: none -- Success: 204, the empty body -- Errors: 404 
- Method: POST -- Path: /api/entries/`<id>`/review -- Request body: none -- Success: 200, the entry wit ai_review set -- Errors: 400 (approach empty), 404 
- GET / serves frontend/index.html. Other frontend files are served from the same folder.
- `<id>` is an integer route parameter. Non-integer ids fall through to a JSON 404.
- The review endpoint returns 400 with {"error": "Add approach text to enable AI review."} when the stored approach is empty or only whitespace. Calling it again replaces the existing review.
Database schema (Phase 2)
- Column: id -- Type: INTEGER -- Constraints: PRIMARY KEY AUTOINCREMENT
- Column: problem_name -- Type: TEXT -- Constraints: NOT NULL
- Column: source -- Type: TEXT -- Constraints: NOT NULL, CHECK in (LeetCode, HackerRank, NeetCode, other)
- Column: topic -- Type: TEXT -- Constraints: NOT NULL DEFAULT "
- Column: difficulty -- Type: TEXT -- Constraints: NOT NULL, CHECK in (Easy, Medium, Hard)
- Column: result -- Type: TEXT -- Constraints: NOT NULL, CHECK in (Solved, Partial, Failed)
- Column: time_minutes -- Type: INTEGER -- Constraints: NOT NULL, CHECK between 1 and 600
- Column: approach -- Type: TEXT -- Constraints: NOT NULL DEFAULT "
- Column: struggles -- Type: TEXT -- Constraints: NOT NULL DEFAULT "
- Column: ai_review -- Type: TEXT -- Constraints: NULL allowed, JSON text
- Column: created_at -- Type: TEXT -- Constraints: NOT NULL
## 4. Acceptance Checklist
Frontend
- [x] Exactly one `<h1>`, one `<header>`, one `<main>`, one `<footer>`, and no skipped heading levels.
- [x] No inline style="..." or on...= attributes anywhere in index.html.
- [x] style.css begins with the box-sizing reset, uses no ID selectors, and uses rem for spacing and font sizes.
- [x] Page loads at least 5 entries from GET /api/entries and renders one card each.
- [x] Both card states appear on load: some with an AI summary, some with the empty state.
- [x] Every card is an `<article class="card">` inside a grid or flex container with gap.
- [x] A valid form submission adds a card without a page reload and updates all three stats.
- [x] Submission is blocked, with visible messages and no alert(), for: empty problem name, no time, time of 0, negative time, decimal time, and time above 600.
- [x] Error messages disappear as soon as the user edits the field.
- [x] Edit fills the form, switches to edit mode, and saves in place. Cancel restores add mode with no changes.
- [x] Delete asks for confirmation. Cancelling keeps the card. Confirming removes it and updates the stats.
- [x] Deleting every entry shows the empty-list message and "—" in the stats, with no NaN.
- [x] Send to AI is disabled for the entry with an empty approach.
- [x] Send to AI shows a loading state for about 1.5 seconds, then displays all four summary fields. Double-clicking does not fire two requests.
- [x] Entering `<b>test</b>` or `<script>` in any text field displays it as plain text, including after a page refresh.
- [x] No horizontal scrollbar at 375px width. Two columns at 768px and wider, one column below.
- [x] Hover, focus ring, active, and disabled states are all visibly different on buttons.
- [x] The form section and the entries list scroll independently at 768px and wider.
- [x] Page works when served by Flask at http://localhost:5000 and shows the load-error message when the server is unreachable.
- [x] Browser console is empty in Chrome, Firefox, and Edge.
Frontend-Backend 
- [x] DevTools Network shows 200 for load, 201 for add, 200 for edit and review, and 204 for delete.
- [x] Invalid input sent directly to the API shows the server's message beside the matching field. Invalid input in the browser shows the client message.
- [x] Stopping the server and clicking Add entry shows a form-level message and no console errors, and the entries array is unchanged.
- [x] Entries added, edited, deleted, and reviewed survive a page refresh.
Backend 
- [x] Repo has /backend and /frontend with the files listed in Section 2, and frontend/mock_data.json is gone.
- [x] .gitignore covers pycache/, .pytest_cache/, venv/, .venv/, .env, *.db, and backend/data.json. git status shows none of them staged.
- [x] requirements.txt is UTF-8 and installs with pip install -r requirements.txt in a fresh venv.
- [x] GET /api/entries returns the five seed entries with correct types (id and time_minutes are numbers, ai_review is an object or null).
- [x] POST with a valid body returns 201 and the new entry with the next id.
- [x] POST returns 400 with a "fields" map for: empty body, non-JSON body, empty problem_name, problem_name over 100 characters, invalid source, difficulty, or result, time_minutes of 0, 601, 2.5, "10", true, and null.
- [x] PUT returns 200 with the updated entry, keeps id, created_at, and ai_review, and returns 404 for a missing id and 400 for an invalid body.
- [x] DELETE returns 204 for an existing id and 404 for a missing id.
- [x] GET /api/entries/999 returns 404 as JSON.
- [x] Review returns 200 with a four-field ai_review, 400 for an entry with empty approach, and 404 for a missing id.
- [x] A forced server error returns {"error": "Internal server error."} with 500 and no stack trace in the response.
- [x] Phase 1: changes survive a Ctrl+C and restart through data.json.
- [x] Phase 2: changes survive a Ctrl+C and restart through the SQLite database.
- [x] Phase 2: the entries table shows id as INTEGER PRIMARY KEY AUTOINCREMENT and every query uses ? placeholders.
- [x] Phase 2: seed.py is safe to run twice (the second run seeds nothing).
- [x] SPRINT2.md has the API table, schema table, run and test steps, AI usage log, and persistence reflection.
## 5. Audit Protocol
- Inspect the generated code line by line with git diff --staged before committing.
- Sprint 1 commit order (already done): SPEC.md, mock_data.json, index.html, style.css, then app.js in pieces (load and render, form validation, edit and delete, fake AI), one commit each.
- Sprint 2 commit order, one commit per item with imperative messages that say what and why: update SPEC.md; backend folder, requirements.txt, .gitignore, and seed_data.json move; Flask scaffold; JSON storage layer; validation and canned review; error handler; GET and POST routes; PUT and DELETE routes; review route; frontend load; frontend add and edit; frontend delete and review; schema.sql; SQLite storage layer; seed.py; SPRINT2.md.
- Check an item off only after verifying it in the browser, with curl.exe, or in the sqlite3 shell.
- Record each place the AI broke a MUST line, returned a wrong status code, or missed a validation case, and how it was fixed, for the AI usage log in SPRINT1.md (Sprint 1) and SPRINT2.md (Sprint 2).
- Before submitting, confirm the repo URL is accessible to the instructional team.
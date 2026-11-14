# Sprint 2

## Project Recap
Interview Reflections lets a student record coding interview problem reflections, including their approach, struggles, and results. The workflow is now backed by a Flask API and SQLite persistence so entries and AI reviews survive page refreshes and server restarts.

## API Contract Table
| Method | Endpoint                   | Request body              | Success status                      | Error statuses |
| ------ | -------------------------- | ------------------------- | ----------------------------------- | -------------- |
| GET    | `/api/entries`             | None                      | 200, list of entries                | 500            |
| GET    | `/api/entries/<id>`        | None                      | 200, one entry                      | 404            |
| POST   | `/api/entries`             | The eight editable fields | 201, the new entry with id          | 400            |
| PUT    | `/api/entries/<id>`        | The eight editable fields | 200, the updated entry              | 400, 404       |
| DELETE | `/api/entries/<id>`        | None                      | 204, the empty body                 | 404            |
| POST   | `/api/entries/<id>/review` | None                      | 200, the entry with `ai_review` set | 400, 404       |

## Database Schema
| Column       | Type    | Constraints                                                |
| ------------ | ------- | ---------------------------------------------------------- |
| **id**       | INTEGER | **PRIMARY KEY AUTOINCREMENT**                              |
| problem_name | TEXT    | NOT NULL                                                   |
| source       | TEXT    | NOT NULL, CHECK in (LeetCode, HackerRank, NeetCode, other) |
| topic        | TEXT    | NOT NULL DEFAULT ""                                        |
| difficulty   | TEXT    | NOT NULL, CHECK in (Easy, Medium, Hard)                    |
| result       | TEXT    | NOT NULL, CHECK in (Solved, Partial, Failed)               |
| time_minutes | INTEGER | NOT NULL, CHECK between 1 and 600                          |
| approach     | TEXT    | NOT NULL DEFAULT ""                                        |
| struggles    | TEXT    | NOT NULL DEFAULT ""                                        | 
| ai_review    | TEXT    | NULL allowed, JSON text                                    |
| created_at   | TEXT    | NOT NULL                                                   |

## How to Run & Test

1. Clone the repository and change into the backend directory:
   ```bash
   git clone <repository-url>
   cd <repository-directory>\project\backend
   ```
2. Create and activate a virtual environment on Windows, then install dependencies:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Seed the database and run the Flask server:
   ```powershell
   python seed.py
   python app.py
   ```
4. Open http://localhost:5000, add or edit an entry, stop the server with `Ctrl+C`, restart it, and confirm the data is still there.

## AI Usage Log & Reflection
I used GitHub Copilot in Agent mode with SPEC.md attached as context for every prompt, sending one prompt per commit and reviewing each change with git diff --staged before committing. For example, at one point a provided Copilot with "#SPEC.md Section 2 (Backend: Structure, Backend: Data structures and types, Backend: Persistence). In backend/app.py add a now_iso() helper that returns a UTC string like 2026-10-12T09:15:00Z, plus the six storage functions: get_all_entries, get_entry, create_entry, update_entry, delete_entry, save_review. Phase 1 only: entries are a list of dicts stored in data.json with json.load and json.dump. If data.json does not exist, create it from seed_data.json. New ids are max(existing ids) + 1, or 1 if empty. create_entry sets id, ai_review (None), and created_at itself. update_entry changes only the eight editable fields and never touches id, created_at, or ai_review. delete_entry returns True or False. save_review sets only ai_review. Do not add routes. Edit only backend/app.py." I proceeded to review the changes, to which it worked flawlessly in this example, to which I then committed as "Add JSON error handler." Though Copilot works well a majority of the time, it can very easily make mistakes that require human revision. Specifically, I used Copilot to create the GET, POST, PUT, and DELETE routes. I wasn't familiar with how to test them prior to the frontend, so I asked Claude, which it instructed to split the terminals, with py app.py running on one, and using "curl.exe -i -X POST http://localhost:5000/api/entries/6/review" among other curl.exe requests to receive the appropriate numbers. The numbers returned in the terminal didn't line up with what Claude expected curl.exe to give. I reported this issue to Claude, in which it told me to put "Set-Content -Path "$env:TEMP\valid.json" -Value '{"problem_name":"Test","source":"LeetCode","difficulty":"Easy","result":"Solved","time_minutes":10}'" in the terminal, among a few other similar lines, which ended up making the curl.exe prompts give the proper errors in the terminal. Shortly after in the front end, the network via DevTools provided the correct error codes when adding a new card, deleting a card, editing a card, clicking save changes, clicking 'Send to AI', etc. Overall, I didn't face many issues during this sprint, other than a few minor problems from Copilot that required small revisions, though it is possible the prompts provided, or the context in the SPEC.md file, could have been optimized. 

When utilziing the JSON file, every add, edit, delete, or review loaded the entire list and rewrote the whole file, and ids came from a hand-written max(ids) + 1. Consequently, two overlapping requests could read the same file and one would silently overwrite the other’s change. SQLite fixed these by letting me change a single row with INSERT, UPDATE, or DELETE, assigning ids through AUTOINCREMENT, which also stopped ids from being reused after a delete, and committing each write as a transaction that either fully succeeds or doesn’t happen. Since I kept all storage behind six functions, the swap changed only those functions and left the routes and the frontend untouched.
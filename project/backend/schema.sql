CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_name TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('LeetCode', 'HackerRank', 'NeetCode', 'Other')),
    topic TEXT NOT NULL DEFAULT '',
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    result TEXT NOT NULL CHECK (result IN ('Solved', 'Partial', 'Failed')),
    time_minutes INTEGER NOT NULL CHECK (time_minutes BETWEEN 1 AND 600),
    approach TEXT NOT NULL DEFAULT '',
    struggles TEXT NOT NULL DEFAULT '',
    ai_review TEXT,
    created_at TEXT NOT NULL
);

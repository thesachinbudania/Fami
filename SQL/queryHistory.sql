sqlite3 fami.db;
CREATE TABLE account_info (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL UNIQUE,
nick_name TEXT,
hash TEXT
);

CREATE TABLE members (
family_id INTEGER,
name TEXT NOT NULL,
contact TEXT NOT NULL,
email TEXT NOT NULL
);
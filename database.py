import sqlite3

class Database:
    def __init__(self, db_file="notes.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                note_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        self.conn.commit()

    def add_user(self, user_id, username=""):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        self.conn.commit()

    def add_note(self, user_id, note_text):
        self.cursor.execute("INSERT INTO notes (user_id, note_text) VALUES (?, ?)", (user_id, note_text))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_notes(self, user_id):
        self.cursor.execute("SELECT id, note_text, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return self.cursor.fetchall()

    def delete_note(self, note_id, user_id):
        self.cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def close(self):
        self.conn.close()


class PasswordDatabase:
    def __init__(self, db_file="passwords.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                password TEXT,
                length INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        self.conn.commit()

    def add_user(self, user_id, username=""):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        self.conn.commit()

    def add_password(self, user_id, password, length):
        self.cursor.execute("INSERT INTO passwords (user_id, password, length) VALUES (?, ?, ?)", (user_id, password, length))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_passwords(self, user_id, limit=20):
        self.cursor.execute("SELECT id, password, length, created_at FROM passwords WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
        return self.cursor.fetchall()

    def get_all_passwords(self, user_id):
        self.cursor.execute("SELECT id, password, length, created_at FROM passwords WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return self.cursor.fetchall()

    def delete_password(self, password_id, user_id):
        self.cursor.execute("DELETE FROM passwords WHERE id = ? AND user_id = ?", (password_id, user_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_all_passwords(self, user_id):
        self.cursor.execute("DELETE FROM passwords WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return self.cursor.rowcount

    def close(self):
        self.conn.close()
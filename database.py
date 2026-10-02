import sqlite3

DB_NAME = "question_bank.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade_level TEXT NOT NULL,
            topic TEXT NOT NULL,
            subtopic TEXT,
            school_name TEXT NOT NULL,
            year TEXT NOT NULL DEFAULT '2026',
            assessment_type TEXT NOT NULL DEFAULT 'Unit Test',
            marks INTEGER DEFAULT 1
        )
    ''')
    
    # Automatically migration guard for missing columns
    cursor.execute("PRAGMA table_info(questions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "year" not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN year TEXT NOT NULL DEFAULT '2026'")
    if "assessment_type" not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN assessment_type TEXT NOT NULL DEFAULT 'Unit Test'")
        
    conn.commit()
    conn.close()
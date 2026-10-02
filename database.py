import sqlite3

DB_NAME = "question_bank.db"

def init_db():
    """Initializes the SQLite database table with columns for tags, school, year, and assessment types."""
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
            marks INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Auto-migration check: ensures missing columns are added if an older DB exists
    cursor.execute("PRAGMA table_info(questions)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    if "year" not in existing_columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN year TEXT NOT NULL DEFAULT '2026'")
    if "assessment_type" not in existing_columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN assessment_type TEXT NOT NULL DEFAULT 'Unit Test'")
        
    conn.commit()
    conn.close()


def insert_question(question_text, subject, grade_level, topic, subtopic, school_name, year, assessment_type, marks):
    """Inserts a single categorized question into the bank database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (question_text, subject, grade_level, topic, subtopic, school_name, year, assessment_type, marks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (question_text, subject, grade_level, topic, subtopic, school_name, str(year), assessment_type, int(marks)))
    conn.commit()
    conn.close()


def get_questions_by_assessment(assessment_type, subject="All", grade="All", topic=""):
    """Retrieves questions organized by assessment tab (Unit Test, Mid-Term, Trial, Annual, Board)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, question_text, subject, grade_level, topic, subtopic, school_name, year, marks FROM questions WHERE assessment_type = ?"
    params = [assessment_type]

    if subject and subject != "All":
        query += " AND subject = ?"
        params.append(subject)
    if grade and grade != "All":
        query += " AND grade_level = ?"
        params.append(grade)
    if topic:
        query += " AND topic LIKE ?"
        params.append(f"%{topic}%")

    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_questions(subject="All", grade="All"):
    """Retrieves questions across all assessment types for Lopon AI synthesis."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, question_text, subject, grade_level, topic, subtopic, school_name, year, assessment_type, marks FROM questions WHERE 1=1"
    params = []

    if subject and subject != "All":
        query += " AND subject = ?"
        params.append(subject)
    if grade and grade != "All":
        query += " AND grade_level = ?"
        params.append(grade)

    query += " ORDER BY topic ASC, id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_question(question_id):
    """Deletes a question by its database ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
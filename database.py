"""Database adapter.
Default: SQLite for a quick local demo. Set DB_MODE=oracle and Oracle environment
variables to use the Oracle tables/procedures supplied in sql/oracle_setup.sql.
"""
import os, sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "examiq.db")
DB_MODE = os.getenv("DB_MODE", "sqlite").lower()

def _oracle_connection():
    import oracledb
    return oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"]
    )

def get_connection():
    if DB_MODE == "oracle":
        return _oracle_connection()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if DB_MODE == "oracle":
        # Oracle schema is created by running sql/oracle_setup.sql once.
        return
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            mathematics INTEGER NOT NULL,
            computer_science INTEGER NOT NULL,
            physics INTEGER NOT NULL,
            english INTEGER NOT NULL,
            dbms INTEGER NOT NULL
        )""")
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            demo_rows = [
                ("EQ1001", "Aarav Mehta", 88, 91, 84, 79, 95),
                ("EQ1002", "Diya Sharma", 76, 82, 80, 88, 79),
                ("EQ1003", "Kabir Singh", 54, 61, 58, 72, 63),
                ("EQ1004", "Ananya Verma", 92, 94, 89, 90, 96),
                ("EQ1005", "Rohan Gupta", 38, 45, 41, 55, 49),
                ("EQ1006", "Meera Kapoor", 67, 73, 70, 81, 74),
            ]
            conn.executemany("INSERT INTO students(student_code,name,mathematics,computer_science,physics,english,dbms) VALUES(?,?,?,?,?,?,?)", demo_rows)

def _row_to_student(row):
    if not row:
        return None
    if isinstance(row, sqlite3.Row):
        scores = [row["mathematics"], row["computer_science"], row["physics"], row["english"], row["dbms"]]
        result = dict(row)
    else:
        keys = ["id","student_code","name","mathematics","computer_science","physics","english","dbms"]
        result = dict(zip(keys, row))
        scores = list(result[k] for k in keys[3:])
    total = sum(scores)
    result["scores"] = scores
    result["total"] = total
    result["percentage"] = round(total / 5, 1)
    result["grade"] = "A" if total >= 400 else "B" if total >= 300 else "C" if total >= 200 else "Needs Support"
    return result

def get_students():
    with get_connection() as conn:
        if DB_MODE == "oracle":
            cur = conn.cursor()
            cur.execute("SELECT student_id, student_code, student_name, mathematics, computer_science, physics, english, dbms FROM examiq_students")
            return [_row_to_student(row) for row in cur.fetchall()]
        rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
        return [_row_to_student(row) for row in rows]

def get_student(student_id):
    with get_connection() as conn:
        if DB_MODE == "oracle":
            cur = conn.cursor()
            cur.execute("SELECT student_id, student_code, student_name, mathematics, computer_science, physics, english, dbms FROM examiq_students WHERE student_id=:id", {"id":student_id})
            return _row_to_student(cur.fetchone())
        return _row_to_student(conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone())

def save_student(student_id, code, name, scores):
    columns = ["mathematics","computer_science","physics","english","dbms"]
    if DB_MODE == "oracle":
        with get_connection() as conn:
            cur = conn.cursor()
            if student_id:
                cur.execute("UPDATE examiq_students SET student_code=:c, student_name=:n, mathematics=:a, computer_science=:b, physics=:p, english=:e, dbms=:d WHERE student_id=:id",
                            {"c":code,"n":name,"a":scores[0],"b":scores[1],"p":scores[2],"e":scores[3],"d":scores[4],"id":student_id})
            else:
                cur.execute("INSERT INTO examiq_students(student_code,student_name,mathematics,computer_science,physics,english,dbms) VALUES(:c,:n,:a,:b,:p,:e,:d)",
                            {"c":code,"n":name,"a":scores[0],"b":scores[1],"p":scores[2],"e":scores[3],"d":scores[4]})
            conn.commit()
        return
    with get_connection() as conn:
        if student_id:
            conn.execute("UPDATE students SET student_code=?, name=?, mathematics=?, computer_science=?, physics=?, english=?, dbms=? WHERE id=?",
                         (code,name,*scores,student_id))
        else:
            conn.execute("INSERT INTO students(student_code,name,mathematics,computer_science,physics,english,dbms) VALUES(?,?,?,?,?,?,?)",
                         (code,name,*scores))

def delete_student(student_id):
    with get_connection() as conn:
        if DB_MODE == "oracle":
            conn.cursor().execute("DELETE FROM examiq_students WHERE student_id=:id", {"id":student_id})
            conn.commit()
        else:
            conn.execute("DELETE FROM students WHERE id=?", (student_id,))

def get_summary():
    students = get_students()
    if not students:
        return {"students":0,"class_average":0,"top_score":0,"top_name":"—","pass_rate":0,"needs_support":0}
    top = max(students, key=lambda s:s["total"])
    return {
        "students":len(students),
        "class_average":round(sum(s["percentage"] for s in students)/len(students),1),
        "top_score":top["total"],"top_name":top["name"],
        "pass_rate":round(sum(s["percentage"] >= 40 for s in students)*100/len(students)),
        "needs_support":sum(s["percentage"] < 40 for s in students)
    }

def get_subject_averages():
    students = get_students()
    keys = ["mathematics","computer_science","physics","english","dbms"]
    return {key: round(sum(s[key] for s in students)/len(students),1) if students else 0 for key in keys}

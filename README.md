# ExamIQ — Smart Examination & Performance Analyzer

A beginner-friendly mini project combining **C++ backend logic**, **Python Flask interface**, and **Oracle PL/SQL database/reporting**.

## Features
- Add, edit, and delete student marks for five subjects
- Automatically calculate total, percentage, grade, class average and pass rate
- Rank students by total marks
- Subject-average and score-distribution charts
- Student analysis page calls the C++ program to calculate total/minimum/maximum/average and digit frequency in the student ID
- Oracle schema, view and PL/SQL package included
- Runs immediately in SQLite demo mode; can be switched to Oracle when Oracle DB is available

## 1. Requirements
- Python 3.10+
- C++ compiler supporting C++17 (`g++`, MinGW, or clang++)
- For Oracle mode only: Oracle Database/Oracle XE and `python-oracledb`

## 2. Run on Windows
1. Extract the project folder.
2. Open Command Prompt inside the `ExamIQ` folder.
3. Run `run_windows.bat`.
4. Open the local address shown in the terminal (usually `http://127.0.0.1:5000`).

If `g++` is not installed, the Python interface still runs, but student analysis uses a Python fallback. Install MinGW-w64 and add its `bin` folder to PATH to demonstrate the C++ backend.

## 3. Run on macOS/Linux
```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

Or manually:
```bash
python -m pip install -r requirements.txt
g++ cpp/analytics.cpp -o analytics -std=c++17
python app.py
```

## 4. Use the app
- Click **Add marks** to add a student.
- Each subject is out of 100.
- Click **Analyze** beside a student to view the C++ analytics result.
- Edit or delete a student from the dashboard.
- The dashboard is populated from the database; there are no fake dashboard metrics.

## 5. Use Oracle PL/SQL
The default database is SQLite so that the project is easy to run during development. The included Oracle script is the database submission component.

1. Open `sql/oracle_setup.sql` in Oracle SQL Developer and run it using your project schema.
2. Install Oracle driver:
   ```bash
   python -m pip install oracledb
   ```
3. Set environment variables before starting Flask:
   ```bat
   set DB_MODE=oracle
   set ORACLE_USER=your_schema_user
   set ORACLE_PASSWORD=your_password
   set ORACLE_DSN=localhost:1521/XEPDB1
   python app.py
   ```
   Replace the example DSN with your Oracle connection string. Do not commit real passwords.
4. The Python database adapter will use `EXAMIQ_STUDENTS` for CRUD. `EXAMIQ_STUDENT_RESULTS` provides calculated totals/percentages/grades, and package `EXAMIQ_REPORTS` contains `CLASS_SUMMARY` and `SUBJECT_AVERAGE` reporting procedures that you can demonstrate in SQL Developer.

Example PL/SQL test:
```sql
SET SERVEROUTPUT ON;
DECLARE
  v_count NUMBER;
  v_avg NUMBER;
  v_top NUMBER;
  v_pass NUMBER;
BEGIN
  examiq_reports.class_summary(v_count, v_avg, v_top, v_pass);
  DBMS_OUTPUT.PUT_LINE('Students: ' || v_count);
  DBMS_OUTPUT.PUT_LINE('Average percentage: ' || ROUND(v_avg, 2));
  DBMS_OUTPUT.PUT_LINE('Top total: ' || v_top);
  DBMS_OUTPUT.PUT_LINE('Pass rate: ' || ROUND(v_pass, 2) || '%');
END;
/
```

## 6. How the three technologies are used
- **C++:** `cpp/analytics.cpp` performs score total/minimum/maximum/average and digit-frequency analysis.
- **Python:** `app.py` runs the Flask web interface, validates form inputs, calls C++, and connects to the database adapter.
- **PL/SQL / Oracle:** `sql/oracle_setup.sql` creates the table, result view, and report package for database-side calculations.
- **HTML/CSS/JavaScript:** `templates/` provides the responsive dark dashboard.

## Project scope / honest note
The project supports Oracle CRUD when configured, and the Oracle PL/SQL reporting package is supplied for direct demonstration in SQL Developer. The dashboard summary currently calculates its cards from the rows returned by the active database adapter. To demonstrate PL/SQL specifically, run the included `EXAMIQ_REPORTS` package in SQL Developer as shown above.

# ExamIQ — Viva Preparation Guide

**Project:** ExamIQ — Smart Examination & Performance Analyzer
**Stack:** C++ (analytics engine) · Python (Tkinter GUI + Flask web variant + DB adapter) · Oracle PL/SQL (schema, view, report package)
**Folder:** `C:\Users\acer\OneDrive\Documents\College stuff\All in one project\ExamIQ`

> How to use this file: Part 1 gives the 30-second answer, Part 3 is the "how does it all work" story
> (memorise the diagram and the 9-step click trace), then Parts 4/5/6 are one section per teacher.
> Part 7 has the cross-technology questions, Part 8 the weak spots, Part 9 the final checklist.

---

## Contents

1. [The 30-second answer](#part-1--the-30-second-answer-to-what-is-your-project)
2. [File map — what each file does](#part-2--file-map-what-each-file-is-responsible-for)
3. [How the files connect + one click traced through every layer](#part-3--how-the-files-connect-this-is-the-how-is-it-working-answer)
4. [Python viva](#part-4--python-viva-your-pythonflask-teacher)
5. [C++ viva](#part-5--c-viva-your-c-teacher)
6. [PL/SQL viva](#part-6--plsql-viva-your-dbms-teacher)
7. [Cross-technology questions](#part-7--cross-technology-questions-they-love)
8. [Weak spots — know them before they're found](#part-8--weak-spots-know-them-before-theyre-found)
9. [Final checklist + commands](#part-9--final-checklist--commands)

---

# PART 1 — The 30-second answer to "what is your project?"

> "ExamIQ is a student marks analyzer built on three technologies. **C++** is the calculator — it
> computes total, min, max, average, grade, pass/fail and digit-frequency of the student ID.
> **Python** is the driver — a Tkinter desktop GUI that stores data through a database adapter, calls
> the C++ program as a child process, and draws the dashboards and charts. **PL/SQL** is the database
> layer — an Oracle schema with a table, a computed view, and a report package. The three talk to each
> other through two clean interfaces: **JSON text** between Python and C++, and **SQL** between Python
> and the database."

---

# PART 2 — File map: what each file is responsible for

| File | Layer | What it does | Key entry points |
|---|---|---|---|
| `run_tk.bat` | launcher | Compiles the C++, then starts the GUI | lines 1–4 |
| `cpp\analytics.cpp` | **C++** | Score + digit-frequency engine, prints JSON | `main()` line 116 |
| `analytics.exe` | C++ | The compiled binary Python actually runs | built by `g++` |
| `tk_app.py` | **Python** | Tkinter GUI (6 pages, charts, dark theme) | `ExamIQApp` line 544, `__main__` line 620 |
| `database.py` | **Python** | DB adapter — SQLite *or* Oracle behind one API | `get_connection()` line 19 |
| `examiq.db` | data | SQLite file created/seeded on first run | `init_db()` line 26 |
| `sql\oracle_setup.sql` | **PL/SQL** | Oracle table + view + package | lines 2, 13, 26, 37 |
| `app.py` + `templates\` | Python (alt) | Flask web version of the same app — an *alternative* front end | routes lines 28–82 |
| `README.md` | docs | Setup + PL/SQL demo script | line 66 has a ready-made demo block |

---

# PART 3 — How the files connect (this is the "how is it working" answer)

```
run_tk.bat
   ├── step 1: g++ cpp\analytics.cpp -o analytics.exe -std=c++17   → produces the C++ binary
   └── step 2: python tk_app.py                                    → starts the GUI

tk_app.py  (Python / Tkinter)
   │
   ├── "from database import ..."  ──►  database.py  ──►  examiq.db        (sqlite3, default)
   │                                          └────────►  Oracle           (DB_MODE=oracle)
   │                                                          ▲
   │                                                          └── schema created by
   │                                                              sql\oracle_setup.sql
   │
   └── subprocess.run(["analytics.exe", "analyze", code, m1..m5])
                    └──────────────► analytics.exe   (C++)
                                            │
                    prints JSON to stdout ◄──┘
                                            │
       json.loads() ──► dict ──► labels on the Analysis page
```

**The two glue points to say out loud:**

1. **Python ↔ C++ = process + text.** `tk_app.py` lines 40–52 build an argument list, run the `.exe`
   with `subprocess.run(..., capture_output=True, text=True, timeout=5, check=True)`, and parse
   `result.stdout` with `json.loads()`. This is why the two languages need no shared build or header
   files — the *contract is the JSON string*.
2. **Python ↔ Database = SQL through one adapter.** Every query lives in `database.py`; the GUI never
   writes SQL. It imports **functions** (`get_students`, `save_student`, `init_db`, `get_summary`,
   `get_subject_averages`) at `tk_app.py` lines 15–16. Swapping SQLite for Oracle means changing *one*
   env var — no GUI code changes.

## Trace one click, layer by layer (say it like this in the viva)

*Clicking **Students → select a row → "Analyze (C++)"**:

| Step | Where | What happens |
|---|---|---|
| 1 | `StudentsPage.analyze()` — tk_app.py 262 | Reads the selected Treeview row, converts to `int` |
| 2 | `app.show("analysis")` — tk_app.py 607 | Switches cards via `page.refresh()` + `tkraise()` |
| 3 | `AnalysisPage.analyze_student()` — 444 | Pulls that student's 5 marks from `self.students` (loaded by `get_students()`) |
| 4 | `run_cpp()` — 40 | `subprocess.run` launches **`analytics.exe`** with 8 arguments |
| 5 | C++ `main()` — analytics.cpp 116 | `argc` check, `atoi()` the 5 marks, builds a `Student` object |
| 6 | C++ computes | `totalUsingPointer`, `variadicTotal`, `minimum`, `maximum`, `grade`, `result`, `digitFrequency` |
| 7 | C++ `cout` — 132–149 | Prints `{"total":437,...}` to stdout, `return 0` |
| 8 | Python `run_cpp` — 50 | `json.loads(stdout)` → dict |
| 9 | `AnalysisPage.show_result()` — 451 | Puts values into 6 cards + digit label + redraws the bar canvas |

That's **one** flow covering Python → OS → C++ → back to Python → screen. Everything else
(add/edit/delete, rankings, CSV) is the same pattern without the C++ hop.

---

# PART 4 — PYTHON viva (your Python/Flask teacher)

## 4.1 Concepts actually used, with proof

**1. Classes, inheritance, composition (OOP)**
- `class ExamIQApp(tk.Tk)` — line 544: the main window **inherits** from Tk's root widget.
- `class StudentsPage(tk.Frame)` etc. — each screen **inherits** from `tk.Frame`.
- **Composition**: `self.pages = {...}` (570) holds 6 page objects; the parent passes `self` (the app)
  into each child so children can request navigation — that's a *parent reference*, the standard
  Tkinter pattern.
- **Encapsulation**: `_field()` and `_oracle_connection()` are prefixed `_` = internal helpers by
  convention.

**2. Event-driven programming**
- `mainloop()` (622) is an infinite event loop — the program spends its life waiting for events.
- `command=self.save` (306) — callbacks passed as values.
- `button.bind("<Button-1>", lambda e, k=key: self.show(k))` (585) — low-level event binding.
- **High-probability viva question:** *"Why `k=key` in that lambda?"* Answer: **late binding**.
  Closures capture the *variable*, not its value, so without the default argument all six buttons
  would navigate to the last key. The default argument freezes the value at creation time.

**3. All three geometry managers** (teachers love this)
- `pack()` — sidebar, most layouts (554)
- `grid()` — form fields, cards, chart columns (174, 300)
- `place()` — page stacking: `page.place(in_=self.content, x=0, y=0, relwidth=1, relheight=1)` (592),
  then `tkraise()` to bring one to front. **This is how page switching works without destroying
  widgets.**

**4. Widgets & variables**
- `tk.StringVar` / `textvariable` (291–293, 313) — **data binding**: the Entry widget and the Python
  variable stay in sync automatically.
- `ttk.Treeview` for tables (95), `ttk.Combobox` (395), `ttk.Scrollbar` (99), `ttk.Style` +
  `theme_use("clam")` (596–597) for dark theming.
- `tk.Canvas` + `create_line / create_rectangle / create_text` (106–133) — **custom bar charts drawn
  manually**, no chart library.

**5. Functions, lambdas, comprehensions, sorting**
- `sorted(students, key=lambda s: s["total"], reverse=True)` (216, 375, 505)
- `[averages[k] for k in SUBJECT_KEYS]` (207) — list comprehension
- `zip(columns, widths)` (96), `enumerate(ranked, 1)` (217)
- `"\n".join(...)` (523), f-strings throughout
- `max(averages, key=averages.get)` (507) — using a function as a key argument

**6. Exception handling — three exact styles in your code**
- Specific, narrow: `except (OSError, subprocess.SubprocessError, json.JSONDecodeError)` (51) — the C++
  call
- Type conversion: `except ValueError` for `int(var.get())` (341)
- Broad with message: `except Exception as exc` then show `str(exc)` (349) — duplicate student ID

**7. File I/O + CSV**
- `with open(path, "w", newline="", encoding="utf-8") as fh:` (531) — context manager closes the file;
  `newline=""` prevents blank lines in CSV on Windows.

**8. Modules, `__main__` guard, env config**
- `if __name__ == "__main__":` (620) — code runs only when executed directly, not on import.
- `os.getenv("DB_MODE", "sqlite")` (database.py 9) and `os.environ["ORACLE_USER"]` (14) — **config from
  the environment, secrets never hard-coded**.
- `import` inside a function (`import oracledb` at 12) — **lazy import**, so SQLite users don't need the
  Oracle driver installed.

**9. Database concepts (Python side)**
- `sqlite3.connect` + `conn.row_factory = sqlite3.Row` (23) — rows addressable by column name.
- **Parameterised queries** — `?` (sqlite) and `:name` (Oracle) at lines 83, 96, 114.
  *If asked "how do you prevent SQL injection?"* → **"Never string-concatenate user input; always pass
  values as parameters"** — that's lines 83/96/114.
- `conn.commit()` for writes (98, 112).

## 4.2 Web version (Flask) — if the teacher asks about `app.py`
- `@app.route("/")` **decorators** map URLs to functions (28); `methods=["GET","POST"]` (43) handles
  form submit.
- `render_template("index.html", ...)` + **Jinja2** templating; `{% extends %}`, `{% for %}`, `{{ }}`
  (templates/analysis.html).
- `request.form.get(...)` (49), `redirect(url_for(...))` (58), `flash()` for one-time messages (57),
  `jsonify()` for a JSON API endpoint (82).
- Two routes share one function (`/students/new` and `/students/<id>/edit`, lines 43–44) — the
  `student_id=None` default distinguishes *add* from *edit*.

---

# PART 5 — C++ viva (your C++ teacher)

`analytics.cpp`'s header comment (lines 5–11) lists the six required concepts. Know each one cold:

**1. Arrays — `marks[5]`, `digitCount[10]`**
- `const int SUBJECTS = 5;` (19) — a named constant instead of the magic number 5.
- `int digitCount[10]` (128) — the classic *counting array*: index = digit, value = how many times it
  occurred. `digitFrequency()` (109–113) zeroes it, then walks the ID string and does
  `digitCount[id[i] - '0']++`. **Know why `- '0'` works**: ASCII of `'7'` is 55; subtracting `'0'` (48)
  gives the numeric 7.

**2. Pointers — `totalUsingPointer(const int* arr, int n)`** (58–62)
- `arr` is a pointer to the first element; the array **decays** to a pointer when passed to a function,
  which is *why* you must pass `n` separately.
- `*(arr + i)` is pointer arithmetic — "the value at address arr + i elements". Emphasise: **`i` is
  scaled by `sizeof(int)` automatically**, so `*(arr+i)` = `arr[i]`.
- `const` means the function promises not to modify the caller's array (**const-correctness**).
- `(double)totalUsingPointer(...) / n` (65) — **very likely question: "what if you remove the cast?"**
  → integer division: `437/5` = **87**, not 87.4. The cast forces floating-point division.

**3. Variadic functions — `sumOf / minOf / maxOf`** (23–54)

The four-step `cstdarg` dance, and be able to name all four macros:

```
va_list args;  va_start(args, count);  va_arg(args, int)  ×N   va_end(args);
```

- `count` is the **sentinel** — variadic functions cannot know how many arguments arrived, so you pass
  the count first. `minOf`/`maxOf` seed with `va_arg` before the loop (36, 48) — that's why their loop
  starts at `i = 1`.
- **"Why are variadic functions risky?"** → no type checking at compile time, and the type you ask
  `va_arg` for must match the *promoted* type (`int` — and you cannot pass `std::string` safely through
  `...`).
- **"Why use variadic here instead of just passing the array?"** → the syllabus requires demonstrating
  variadic functions; `variadicTotal()` (83) calls `sumOf(5, marks[0], ..., marks[4])`, deliberately
  duplicating `total()` so the JSON can show **two independent methods agreeing**:
  `"total":437,"variadic_total":437`. That parallel output is the proof.

**4. Class and object — `class Student`** (69–114)
- **Encapsulation**: `private:` `id`, `marks[]` (71–72) — only public methods touch the data.
- **Constructor** (74): takes `const string&` (**pass by const reference** — no copy) and
  `const int values[]`.
- **Const member functions** (79, 80, 83, 94, 102, 109): a trailing `const` promises "I will not modify
  the object". That is why `total()` can be called on a `const Student`.
- **Object creation**: `Student s(studentId, marks);` (126).
- Methods delegate: `total()` → `totalUsingPointer(marks, SUBJECTS)` (79) — the class *wraps* the
  pointer technique.

**5. Loops, conditions, `string`**
- `grade()` (94–100): `if/else-if` ladder — ≥400 A, ≥300 B, ≥200 C, else "Needs Support".
- `result()` (102–106): **early return** — fails on the *first* subject below 33.
- `string` operations: `argv[2]` → `std::string`, `.length()` (111), `[]` indexing, `==` comparison
  (117), `/` in `id[i] >= '0'` char arithmetic.

**6. `main`, `argc`/`argv`, JSON output**
- `int main(int argc, char* argv[])` (116); `argc != 3 + SUBJECTS` = 8 → validates exactly 8 arguments;
  `string(argv[1]) != "analyze"` checks the sub-command.
- `atoi(argv[3+i])` (124) — **string → int**. *"What's the weakness?"* → `atoi` does **no error
  checking** (garbage ⇒ 0). `std::stoi` with try/catch would be the safer answer.
- JSON is printed **manually** (132–149), and the `bool first` flag (141, 145) prevents a trailing
  comma — valid JSON requires no comma before `}`.
- **No `endl` anywhere** — deliberate: newlines would still parse, but clean output keeps `json.loads`
  trivial.
- **`return 0` on success, `return 1` on bad usage** (119) — and Python's `check=True` turns `1` into an
  exception. **Exit codes are part of the contract.**

**7. Compilation** — `g++ cpp\analytics.cpp -o analytics.exe -std=c++17`. Be ready: `-o` names the
output, `-std=c++17` selects the standard, `.cpp → .o (compile) → .exe (link)`.

Expected output to memorise:

```
analytics.exe analyze EQ1001 88 91 84 79 95
{"total":437,"variadic_total":437,"minimum":79,"maximum":95,"average":87.4,"grade":"A","result":"PASS","digit_frequency":{"0":2,"1":2}}
```

---

# PART 6 — PL/SQL viva (your DBMS teacher)

You have **three** PL/SQL objects in `sql\oracle_setup.sql`. Learn the "what and why" of each.

## 6.1 `CREATE TABLE examiq_students` (lines 2–11)

```sql
student_id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
student_code VARCHAR2(30) NOT NULL UNIQUE,
mathematics NUMBER(3) NOT NULL CHECK (mathematics BETWEEN 0 AND 100), ...
```

- `NUMBER(3)` — max 3 digits, i.e. 0–999, right for marks out of 100.
- `VARCHAR2` (not `VARCHAR`) — Oracle's recommended character type.
- `GENERATED BY DEFAULT AS IDENTITY` — **auto-increment** (Oracle 12c+); replaces old
  sequence+trigger.
- `PRIMARY KEY` = unique + not null; `UNIQUE` on `student_code` = business rule "student IDs can't
  repeat" — **and it's enforced by the database, not just by Python**.
- `CHECK ... BETWEEN 0 AND 100` — **declarative integrity**: invalid marks are rejected even if someone
  inserts directly via SQL Developer.
- **"Why constraints if Python already validates?"** → defence in depth; the DB is the last line, and
  other clients (SQL Developer, another app) bypass Python entirely.

## 6.2 `CREATE OR REPLACE VIEW examiq_student_results` (13–24)

- A **view = a stored query**. It doesn't hold data; it computes on read.
- Does three things: `total_marks` (sum of 5), `percentage` (`ROUND(sum/5, 2)`), and `grade` via a
  **`CASE` expression**.
- **"Why a view?"** → **single source of truth** for the grading formula; every client reading the view
  gets identical maths instead of re-implementing it. `CREATE OR REPLACE` = re-runnable script, no
  `DROP` needed.
- Note: `ROUND` returns a rounded number; `NVL(x, 0)` in the package replaces NULL with 0 — **"what
  does NVL do?"** is a guaranteed question.

## 6.3 `CREATE OR REPLACE PACKAGE examiq_reports` + `PACKAGE BODY` (26–63)

- A **package = spec + body**: the spec (26–35) is the *public interface*; the body (37–63) is the
  *implementation*. You can change the body without invalidating callers → **encapsulation +
  reusability**, the PL/SQL equivalent of a C++ class declaration vs definition.
- `class_summary(p_student_count OUT, p_average_percentage OUT, p_top_total OUT, p_pass_rate OUT)` —
  **`OUT` parameters**: PL/SQL has no return-value tuple, so results come back through `OUT` params.
- Inside: `SELECT COUNT(*), NVL(AVG(percentage),0), NVL(MAX(total_marks),0), 100 * AVG(CASE WHEN
  percentage >= 40 THEN 1 ELSE 0 END) INTO p_... FROM examiq_student_results;`
  → **`SELECT ... INTO`** assigns query results to variables; **aggregate functions** `COUNT/AVG/MAX`;
  the `AVG(CASE ... THEN 1 ELSE 0)` trick computes a **pass rate as a percentage**. Explain this one
  slowly — it's the most impressive line in the file.
- `subject_average(p_subject IN VARCHAR2, p_average OUT NUMBER)` (51–61) — a **`CASE` statement**
  dispatching to different `SELECT`s, with `RAISE_APPLICATION_ERROR(-20001, 'Unknown subject')` for
  anything else. **"What is -20001?"** → a **user-defined error number** (allowed range −20000 to
  −20999); `RAISE_APPLICATION_ERROR` throws a custom exception back to the caller.
- `END;` vs `END package_name;` vs the `/` terminator: `/` tells SQL Developer/SQL*Plus to **execute**
  the block. `COMMIT;` (72) makes the 3 sample `INSERT`s permanent.

## 6.4 How to demo it live (do this before the viva)

Oracle isn't installed on this machine, so use **Oracle Live SQL** (https://livesql.oracle.com — free,
browser, no install): paste `sql/oracle_setup.sql` → Run All → then run the anonymous block already
written for you in your **README lines 67–82**:

```sql
SET SERVEROUTPUT ON;
DECLARE
  v_count NUMBER; v_avg NUMBER; v_top NUMBER; v_pass NUMBER;
BEGIN
  examiq_reports.class_summary(v_count, v_avg, v_top, v_pass);
  DBMS_OUTPUT.PUT_LINE('Students: ' || v_count);
  DBMS_OUTPUT.PUT_LINE('Average percentage: ' || ROUND(v_avg, 2));
END;
/
```

That `DECLARE ... BEGIN ... END;` **anonymous block** with `SET SERVEROUTPUT ON` +
`DBMS_OUTPUT.PUT_LINE` is exactly what a PL/SQL examiner wants to see.

---

# PART 7 — Cross-technology questions they love

**"Why three languages instead of one?"**
> Each does what it's best at, and each teacher gets a real component. C++ for compiled computation
> speed and low-level concepts (pointers, arrays); Python for fast UI + DB glue; PL/SQL so
> heavy/aggregate logic runs *inside* the database, close to the data, instead of pulling thousands of
> rows to the app.

**"How do Python and C++ communicate?"**
> One process spawns the other. Python's `subprocess.run` passes arguments, C++ writes a JSON line to
> stdout, Python parses it with `json.loads`. **Loose coupling**: I could replace the C++ engine with a
> Rust binary and Python wouldn't change, as long as the JSON contract held. `timeout=5` and
> `check=True` handle hangs and crashes.

**"Where is the grade formula written?"**
> Honestly: **three places** — C++ `Student::grade()` (94), Python `_row_to_student` (database.py 67),
> and the Oracle view (18–23). That guarantees the demo always works even without C++, but it's
> **duplicated business logic** — the textbook fix is a single source (the DB view) that everyone
> reads. *Saying this yourself earns marks; being caught by it costs marks.*

**"Why is the default SQLite and not Oracle?"**
> So the project runs with **zero setup** in a viva lab. Oracle mode is a config switch
> (`DB_MODE=oracle` + credentials), and the Oracle schema ships as a script. The adapter pattern means
> the GUI never knows which one it's talking to.

---

# PART 8 — Weak spots: know them before they're found

| # | Issue | Honest one-liner if asked |
|---|---|---|
| 1 | **`app.py` (Flask) can't find the exe on Windows** — line 13 joins `"analytics"` with no `.exe`, so `subprocess` raises `FileNotFoundError` and the `except` at 18 **silently falls back to Python**. | "The Tkinter version (`tk_app.py` 43) picks `.exe` by platform; the Flask version has the fallback so it still works. Worth fixing — it means the **web** version never truly exercises C++ on Windows." |
| 2 | **PASS threshold inconsistency**: C++ uses *every subject ≥ 33* (104), Rankings agrees (377), but `class_summary`/`get_summary` count pass as *percentage ≥ 40* (sql 46, database 125). | "Two different definitions — subject-level pass vs overall pass. They should be unified." |
| 3 | **PL/SQL is not called by the app** — `get_summary()` computes in Python; the `examiq_reports` procedures are unused by the GUI. | "The package is demonstrated in SQL Developer/Live SQL as the DB submission; the app computes the same numbers in Python for portability." |
| 4 | **`atoi` has no validation** (C++ 124) | "Input is validated in Python first (`EntryPage.save`, 336–346); `stoi` would be stricter." |
| 5 | **README still describes the Flask app as the main UI** | Minor doc drift after swapping in the Tkinter GUI. |
| 6 | `tk_app.py` is ~620 lines in one file | "Single-file by design for a mini project; the `Page` classes keep it separated and it would split into modules easily." |

---

# PART 9 — Final checklist + commands

## Run it

```bat
:: recompile C++ and launch the GUI
run_tk.bat
```

```bat
:: or step by step
cd /d "C:\Users\acer\OneDrive\Documents\College stuff\All in one project\ExamIQ"
g++ cpp\analytics.cpp -o analytics.exe -std=c++17
python tk_app.py
```

```bat
:: C++ demo on its own
analytics.exe analyze EQ1001 88 91 84 79 95
```

```bat
:: web (Flask) variant instead of the desktop GUI
python app.py        →  http://127.0.0.1:5000
```

## Screens to show, in this order

1. **Dashboard** — cards (students / class average / top score / pass rate), two bar charts, top
   performers table.
2. **Students** — the table; then select *Aarav Mehta* and click **Analyze (C++)**.
3. **C++ Analysis** — total 437, min 79, max 95, average 87.4, grade A, PASS, `digit 0 x 2`,
   `digit 1 x 2`, plus the variadic/pointer totals. **This is the money screen** — it proves all three
   layers in one view.
4. **Marks Entry** — add a student (shows validation: name required, marks 0–100, unique ID).
5. **Rankings** — sorted by total with PASS/FAIL.
6. **Reports → Export CSV** — file writing.
7. **Live SQL** — table + view + `examiq_reports.class_summary` output.

## Practice order

1. Draw the PART 3 diagram from memory, then trace **the 9-step click flow** out loud.
2. **C++**: recite the 6 concepts + the `va_arg` four-step + why the `(double)` cast matters.
3. **PL/SQL**: explain table → view → package spec → body, then run the README demo block on Live SQL
   once so it's muscle memory.
4. **Python**: the `lambda e, k=key` late-binding answer and "how do you stop SQL injection" — those two
   come up almost every time.

---

*Generated from the actual source files in this folder. If the code changes, re-check the line numbers.*

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os, json, subprocess
from database import init_db, get_connection, get_students, save_student, delete_student, get_subject_averages, get_summary, get_student

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "examiq-local-demo-key")
init_db()

SUBJECTS = ["Mathematics", "Computer Science", "Physics", "English", "DBMS"]

def cpp_analyze(scores, student_id=""):
    """Call the C++ analytics executable. Falls back to Python if it has not been compiled."""
    executable = os.path.join(os.path.dirname(__file__), "analytics")
    args = [executable, "analyze", str(student_id)] + [str(int(x)) for x in scores]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=3, check=True)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        values = [int(x) for x in scores]
        return {
            "total": sum(values),
            "minimum": min(values) if values else 0,
            "maximum": max(values) if values else 0,
            "average": round(sum(values) / len(values), 2) if values else 0,
            "digit_frequency": {}
        }

@app.route("/")
def dashboard():
    students = get_students()
    summary = get_summary()
    subject_averages = get_subject_averages()
    ranked = sorted(students, key=lambda s: s["total"], reverse=True)
    distribution = [0] * 5
    for student in students:
        pct = student["percentage"]
        idx = min(int(pct // 20), 4)
        distribution[idx] += 1
    return render_template("index.html", students=ranked, summary=summary,
                           subject_averages=subject_averages, distribution=distribution,
                           subjects=SUBJECTS)

@app.route("/students/new", methods=["GET", "POST"])
@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def student_form(student_id=None):
    existing = get_student(student_id) if student_id else None
    if request.method == "POST":
        try:
            sid = request.form.get("student_code", "").strip()
            name = request.form.get("name", "").strip()
            scores = [int(request.form.get(f"score{i}", "0")) for i in range(1, 6)]
            if not sid or not name:
                raise ValueError("Student ID and name are required.")
            if any(score < 0 or score > 100 for score in scores):
                raise ValueError("Each subject mark must be between 0 and 100.")
            save_student(student_id, sid, name, scores)
            flash("Student marks saved successfully.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception as exc:
            flash("Could not save marks. Check that the student ID is unique. " + str(exc), "error")
    return render_template("student_form.html", student=existing, subjects=SUBJECTS)

@app.route("/students/<int:student_id>/delete", methods=["POST"])
def student_delete(student_id):
    delete_student(student_id)
    flash("Student record deleted.", "success")
    return redirect(url_for("dashboard"))

@app.route("/students/<int:student_id>/analysis")
def student_analysis(student_id):
    student = get_student(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("dashboard"))
    analysis = cpp_analyze(student["scores"], student["student_code"])
    return render_template("analysis.html", student=student, analysis=analysis, subjects=SUBJECTS)

@app.route("/api/summary")
def api_summary():
    return jsonify({"summary": get_summary(), "subject_averages": get_subject_averages()})

if __name__ == "__main__":
    app.run(debug=True)

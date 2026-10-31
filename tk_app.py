"""ExamIQ - Smart Examination & Performance Analyzer (Tkinter desktop version)

Python (Tkinter)  -> user interface and integration
C++ (analytics)   -> computing aptitude backend, called with subprocess
Database          -> database.py (SQLite for testing, Oracle PL/SQL for final demo)
"""
import os
import sys
import csv
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from database import (init_db, get_students, get_student, save_student,
                      delete_student, get_summary, get_subject_averages)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBJECTS = ["Mathematics", "Computer Science", "Physics", "English", "DBMS"]
SUBJECT_KEYS = ["mathematics", "computer_science", "physics", "english", "dbms"]

# ---------- dark theme colours ----------
BG = "#080d16"
SIDEBAR = "#0b1220"
PANEL = "#0e1626"
BORDER = "#1e293b"
TEXT = "#e5edf7"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
GREEN = "#34d399"
VIOLET = "#a78bfa"
AMBER = "#fbbf24"
RED = "#f87171"
FONT = "Segoe UI"


# =====================================================================
#  Python <-> C++ connection
# =====================================================================
def run_cpp(student_code, scores):
    """Run analytics.exe with subprocess and return its JSON output as a dict.
    Returns None and an error message if the C++ program cannot be run."""
    exe_name = "analytics.exe" if sys.platform.startswith("win") else "analytics"
    exe_path = os.path.join(BASE_DIR, exe_name)
    if not os.path.exists(exe_path):
        return None, "analytics.exe not found. Compile it first (see README)."
    args = [exe_path, "analyze", str(student_code)] + [str(int(s)) for s in scores]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5, check=True)
        return json.loads(result.stdout), ""
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return None, "C++ program failed: " + str(exc)


# =====================================================================
#  Small reusable widgets
# =====================================================================
def make_button(parent, text, command, kind="primary"):
    colors = {
        "primary": (ACCENT, "#06111c"),
        "secondary": ("#111827", "#dbeafe"),
        "danger": ("#27131b", "#fca5a5"),
    }
    bg, fg = colors[kind]
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     activebackground=bg, activeforeground=fg, relief="flat",
                     font=(FONT, 10, "bold"), padx=14, pady=7, cursor="hand2", bd=0)


def make_card(parent, title, color):
    """A statistics card. Returns (frame, value_label, sub_label)."""
    frame = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
    tk.Label(frame, text=title.upper(), bg=PANEL, fg=MUTED,
             font=(FONT, 8, "bold")).pack(anchor="w", padx=16, pady=(14, 0))
    value = tk.Label(frame, text="-", bg=PANEL, fg=color, font=(FONT, 24, "bold"))
    value.pack(anchor="w", padx=16, pady=(4, 0))
    sub = tk.Label(frame, text="", bg=PANEL, fg=MUTED, font=(FONT, 9))
    sub.pack(anchor="w", padx=16, pady=(0, 14))
    return frame, value, sub


def make_panel(parent, title, subtitle=""):
    frame = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
    tk.Label(frame, text=title, bg=PANEL, fg="white",
             font=(FONT, 12, "bold")).pack(anchor="w", padx=16, pady=(14, 0))
    if subtitle:
        tk.Label(frame, text=subtitle, bg=PANEL, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w", padx=16)
    return frame


def make_table(parent, columns, widths, height=10):
    """A dark Treeview table with a scrollbar. columns = list of heading names."""
    holder = tk.Frame(parent, bg=PANEL)
    tree = ttk.Treeview(holder, columns=columns, show="headings", height=height)
    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="w")
    scroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return holder, tree


def draw_bar_chart(canvas, labels, values, maximum, colors):
    """Draw a simple bar chart on a Tkinter Canvas."""
    canvas.delete("all")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    if w < 50 or h < 50:
        return
    left, right, top, bottom = 40, 15, 15, 38
    plot_h = h - top - bottom
    plot_w = w - left - right
    # grid lines and y labels
    for i in range(5):
        y = top + plot_h * i / 4
        canvas.create_line(left, y, w - right, y, fill=BORDER)
        canvas.create_text(left - 8, y, text=str(int(maximum - maximum * i / 4)),
                           fill=MUTED, font=(FONT, 8), anchor="e")
    n = len(values)
    slot = plot_w / max(n, 1)
    bar_w = min(slot * 0.55, 52)
    for i, (label, value) in enumerate(zip(labels, values)):
        x_center = left + slot * i + slot / 2
        bar_h = plot_h * (value / maximum) if maximum else 0
        canvas.create_rectangle(x_center - bar_w / 2, top + plot_h - bar_h,
                                x_center + bar_w / 2, top + plot_h,
                                fill=colors[i % len(colors)], outline="")
        canvas.create_text(x_center, top + plot_h - bar_h - 9, text=str(value),
                           fill=TEXT, font=(FONT, 9, "bold"))
        canvas.create_text(x_center, h - bottom + 16, text=label,
                           fill=MUTED, font=(FONT, 8))


class ChartCanvas(tk.Canvas):
    """Canvas that redraws its bar chart whenever the window is resized."""
    def __init__(self, parent, colors):
        super().__init__(parent, bg=PANEL, highlightthickness=0, height=240)
        self.colors = colors
        self.data = ([], [], 100)
        self.bind("<Configure>", lambda e: self.redraw())

    def set_data(self, labels, values, maximum):
        self.data = (labels, values, maximum)
        self.redraw()

    def redraw(self):
        labels, values, maximum = self.data
        draw_bar_chart(self, labels, values, maximum, self.colors)


# =====================================================================
#  Pages
# =====================================================================
class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        tk.Label(self, text="EXECUTIVE SNAPSHOT", bg=BG, fg=ACCENT,
                 font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Label(self, text="Class performance", bg=BG, fg="white",
                 font=(FONT, 22, "bold")).pack(anchor="w", pady=(2, 14))

        cards = tk.Frame(self, bg=BG)
        cards.pack(fill="x")
        self.cards = {}
        for i, (key, title, color) in enumerate([
                ("students", "Students", "white"),
                ("average", "Class average", ACCENT),
                ("top", "Top score", GREEN),
                ("pass", "Pass rate", VIOLET)]):
            frame, value, sub = make_card(cards, title, color)
            frame.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            cards.columnconfigure(i, weight=1, uniform="card")
            self.cards[key] = (value, sub)

        charts = tk.Frame(self, bg=BG)
        charts.pack(fill="x", pady=14)
        charts.columnconfigure(0, weight=3, uniform="c")
        charts.columnconfigure(1, weight=2, uniform="c")
        left = make_panel(charts, "Subject averages", "Class mean out of 100")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.subject_chart = ChartCanvas(left, [ACCENT, VIOLET, GREEN, AMBER, "#818cf8"])
        self.subject_chart.pack(fill="both", expand=True, padx=10, pady=10)
        right = make_panel(charts, "Score distribution", "Number of students by percentage")
        right.grid(row=0, column=1, sticky="nsew")
        self.dist_chart = ChartCanvas(right, [RED, "#fb923c", AMBER, ACCENT, GREEN])
        self.dist_chart.pack(fill="both", expand=True, padx=10, pady=10)

        top = make_panel(self, "Top performers", "Highest total marks")
        top.pack(fill="both", expand=True)
        holder, self.tree = make_table(top, ["Rank", "Student", "Student ID", "Total", "Percentage"],
                                       [60, 260, 140, 90, 120], height=5)
        holder.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh(self):
        summary = get_summary()
        students = get_students()
        v, s = self.cards["students"]; v.config(text=summary["students"]); s.config(text="Records in database")
        v, s = self.cards["average"]; v.config(text=f'{summary["class_average"]}%'); s.config(text="Mean percentage")
        v, s = self.cards["top"]; v.config(text=summary["top_score"]); s.config(text=summary["top_name"])
        v, s = self.cards["pass"]; v.config(text=f'{summary["pass_rate"]}%'); s.config(text=f'{summary["needs_support"]} below 40%')

        averages = get_subject_averages()
        self.subject_chart.set_data(["Maths", "Comp Sci", "Physics", "English", "DBMS"],
                                    [averages[k] for k in SUBJECT_KEYS], 100)
        distribution = [0] * 5
        for st in students:
            distribution[min(int(st["percentage"] // 20), 4)] += 1
        top_count = max(max(distribution), 1)
        self.dist_chart.set_data(["0-19", "20-39", "40-59", "60-79", "80-100"],
                                 distribution, top_count)

        self.tree.delete(*self.tree.get_children())
        ranked = sorted(students, key=lambda x: x["total"], reverse=True)[:5]
        for i, st in enumerate(ranked, 1):
            self.tree.insert("", "end", values=(f"#{i}", st["name"], st["student_code"],
                                                st["total"], f'{st["percentage"]}%'))


class StudentsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text="Student records", bg=BG, fg="white",
                 font=(FONT, 22, "bold")).pack(side="left")
        make_button(header, "Delete", self.delete, "danger").pack(side="right")
        make_button(header, "Analyze (C++)", self.analyze, "secondary").pack(side="right", padx=8)
        make_button(header, "Edit marks", self.edit, "secondary").pack(side="right")
        make_button(header, "+ Add student", lambda: app.show("entry"), "primary").pack(side="right", padx=8)

        panel = make_panel(self, "All students", "Select a row, then use the buttons above")
        panel.pack(fill="both", expand=True)
        columns = ["ID", "Student ID", "Name"] + SUBJECTS + ["Total", "Percentage", "Grade"]
        widths = [40, 90, 150, 90, 120, 70, 70, 60, 60, 90, 110]
        holder, self.tree = make_table(panel, columns, widths, height=16)
        holder.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for st in get_students():
            self.tree.insert("", "end", iid=str(st["id"]),
                             values=[st["id"], st["student_code"], st["name"]] + st["scores"] +
                                    [st["total"], f'{st["percentage"]}%', st["grade"]])

    def selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("ExamIQ", "Please select a student first.")
            return None
        return int(selection[0])

    def edit(self):
        sid = self.selected_id()
        if sid:
            self.app.pages["entry"].load(get_student(sid))
            self.app.show("entry")

    def analyze(self):
        sid = self.selected_id()
        if sid:
            self.app.show("analysis")
            self.app.pages["analysis"].analyze_student(sid)

    def delete(self):
        sid = self.selected_id()
        if sid and messagebox.askyesno("Delete", "Delete this student record?"):
            delete_student(sid)
            self.app.refresh_all()


class EntryPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.editing_id = None
        self.title = tk.Label(self, text="Add student marks", bg=BG, fg="white",
                              font=(FONT, 22, "bold"))
        self.title.pack(anchor="w")
        tk.Label(self, text="Enter marks out of 100 for each of the five subjects.",
                 bg=BG, fg=MUTED, font=(FONT, 10)).pack(anchor="w", pady=(2, 14))

        form = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        form.pack(anchor="w", fill="x")
        inner = tk.Frame(form, bg=PANEL)
        inner.pack(fill="x", padx=22, pady=20)

        self.code_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.mark_vars = [tk.StringVar() for _ in SUBJECTS]

        self._field(inner, "Student ID", self.code_var, 0, 0)
        self._field(inner, "Student name", self.name_var, 0, 1)
        tk.Label(inner, text="Subject marks", bg=PANEL, fg="white",
                 font=(FONT, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(18, 4))
        for i, subject in enumerate(SUBJECTS):
            self._field(inner, f"{subject} (/100)", self.mark_vars[i], 3 + i // 2, i % 2)
        inner.columnconfigure(0, weight=1, uniform="f")
        inner.columnconfigure(1, weight=1, uniform="f")

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(anchor="e", fill="x", pady=14)
        make_button(buttons, "Save marks", self.save, "primary").pack(side="right")
        make_button(buttons, "Clear", self.clear, "secondary").pack(side="right", padx=8)

    def _field(self, parent, label, variable, row, col):
        box = tk.Frame(parent, bg=PANEL)
        box.grid(row=row, column=col, sticky="ew", padx=(0, 14), pady=6)
        tk.Label(box, text=label, bg=PANEL, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Entry(box, textvariable=variable, bg=BG, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FONT, 11), highlightbackground="#334155",
                 highlightcolor=ACCENT, highlightthickness=1).pack(fill="x", ipady=6, pady=(4, 0))

    def clear(self):
        self.editing_id = None
        self.title.config(text="Add student marks")
        self.code_var.set("")
        self.name_var.set("")
        for var in self.mark_vars:
            var.set("")

    def load(self, student):
        self.editing_id = student["id"]
        self.title.config(text="Edit student marks")
        self.code_var.set(student["student_code"])
        self.name_var.set(student["name"])
        for var, score in zip(self.mark_vars, student["scores"]):
            var.set(str(score))

    def save(self):
        code = self.code_var.get().strip()
        name = self.name_var.get().strip()
        if not code or not name:
            messagebox.showerror("Missing details", "Student ID and name are required.")
            return
        try:
            scores = [int(var.get()) for var in self.mark_vars]
        except ValueError:
            messagebox.showerror("Invalid marks", "Marks must be whole numbers.")
            return
        if any(score < 0 or score > 100 for score in scores):
            messagebox.showerror("Invalid marks", "Each mark must be between 0 and 100.")
            return
        try:
            save_student(self.editing_id, code, name, scores)
        except Exception as exc:
            messagebox.showerror("Could not save", "Check that the Student ID is unique.\n\n" + str(exc))
            return
        messagebox.showinfo("ExamIQ", "Student marks saved successfully.")
        self.clear()
        self.app.refresh_all()
        self.app.show("students")

    def refresh(self):
        pass


class RankingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        tk.Label(self, text="Student rankings", bg=BG, fg="white",
                 font=(FONT, 22, "bold")).pack(anchor="w", pady=(0, 14))
        panel = make_panel(self, "Ranking by total marks", "Highest first (out of 500)")
        panel.pack(fill="both", expand=True)
        holder, self.tree = make_table(panel, ["Rank", "Student", "Student ID", "Total / 500",
                                               "Percentage", "Grade", "Result"],
                                       [60, 220, 120, 100, 110, 120, 90], height=16)
        holder.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        ranked = sorted(get_students(), key=lambda x: x["total"], reverse=True)
        for i, st in enumerate(ranked, 1):
            result = "PASS" if min(st["scores"]) >= 33 else "FAIL"
            self.tree.insert("", "end", values=(f"#{i}", st["name"], st["student_code"],
                                                st["total"], f'{st["percentage"]}%',
                                                st["grade"], result))


class AnalysisPage(tk.Frame):
    """Shows the output of the C++ program for one student."""
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.students = []
        tk.Label(self, text="C++ ANALYSIS MODULE", bg=BG, fg=ACCENT,
                 font=(FONT, 9, "bold")).pack(anchor="w")
        tk.Label(self, text="Student analysis", bg=BG, fg="white",
                 font=(FONT, 22, "bold")).pack(anchor="w", pady=(2, 12))

        picker = tk.Frame(self, bg=BG)
        picker.pack(fill="x")
        self.combo = ttk.Combobox(picker, state="readonly", width=40, font=(FONT, 10))
        self.combo.pack(side="left")
        make_button(picker, "Run C++ analysis", self.run_selected, "primary").pack(side="left", padx=10)
        self.status = tk.Label(self, text="", bg=BG, fg=MUTED, font=(FONT, 9))
        self.status.pack(anchor="w", pady=(8, 8))

        cards = tk.Frame(self, bg=BG)
        cards.pack(fill="x")
        self.cards = {}
        titles = [("total", "Total marks", ACCENT), ("minimum", "Minimum", AMBER),
                  ("maximum", "Maximum", GREEN), ("average", "Average", VIOLET),
                  ("grade", "Grade", "white"), ("result", "Result", GREEN)]
        for i, (key, title, color) in enumerate(titles):
            frame, value, _ = make_card(cards, title, color)
            frame.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            cards.columnconfigure(i, weight=1, uniform="a")
            self.cards[key] = value

        lower = tk.Frame(self, bg=BG)
        lower.pack(fill="both", expand=True, pady=14)
        lower.columnconfigure(0, weight=3, uniform="l")
        lower.columnconfigure(1, weight=2, uniform="l")
        self.marks_panel = make_panel(lower, "Subject score breakdown")
        self.marks_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.marks_canvas = tk.Canvas(self.marks_panel, bg=PANEL, highlightthickness=0)
        self.marks_canvas.pack(fill="both", expand=True, padx=12, pady=12)
        self.marks_canvas.bind("<Configure>", lambda e: self.draw_marks())
        self.current_scores = [0] * 5

        digits = make_panel(lower, "Student ID digit frequency", "Calculated by the C++ backend")
        digits.grid(row=0, column=1, sticky="nsew")
        self.digit_label = tk.Label(digits, text="", bg=PANEL, fg=ACCENT,
                                    font=("Consolas", 13, "bold"), justify="left")
        self.digit_label.pack(anchor="w", padx=16, pady=14)
        self.variadic_label = tk.Label(digits, text="", bg=PANEL, fg=MUTED,
                                       font=(FONT, 9), justify="left", wraplength=300)
        self.variadic_label.pack(anchor="w", padx=16)

    def refresh(self):
        self.students = get_students()
        self.combo["values"] = [f'{s["student_code"]}  -  {s["name"]}' for s in self.students]
        if self.students and self.combo.current() < 0:
            self.combo.current(0)

    def run_selected(self):
        index = self.combo.current()
        if index >= 0:
            self.show_result(self.students[index])

    def analyze_student(self, student_id):
        self.refresh()
        for i, st in enumerate(self.students):
            if st["id"] == student_id:
                self.combo.current(i)
                self.show_result(st)

    def show_result(self, student):
        data, error = run_cpp(student["student_code"], student["scores"])
        self.current_scores = student["scores"]
        self.draw_marks()
        if data is None:
            self.status.config(text=error, fg=RED)
            return
        self.status.config(text=f'Result for {student["name"]} computed by the C++ program.', fg=GREEN)
        for key, label in self.cards.items():
            label.config(text=str(data[key]))
        self.cards["result"].config(fg=GREEN if data["result"] == "PASS" else RED)
        freq = data["digit_frequency"]
        self.digit_label.config(text="\n".join(f"digit {d}  x {c}" for d, c in freq.items())
                                or "No digits in this ID.")
        self.variadic_label.config(
            text=f'Variadic function sumOf() total = {data["variadic_total"]}\n'
                 f'Pointer-based total = {data["total"]}')

    def draw_marks(self):
        c = self.marks_canvas
        c.delete("all")
        w = c.winfo_width()
        if w < 100:
            return
        for i, subject in enumerate(SUBJECTS):
            y = 12 + i * 38
            score = self.current_scores[i]
            c.create_text(0, y + 8, text=subject, fill=TEXT, font=(FONT, 10), anchor="w")
            c.create_text(w - 4, y + 8, text=f"{score}/100", fill=ACCENT,
                          font=("Consolas", 10, "bold"), anchor="e")
            c.create_rectangle(0, y + 20, w - 4, y + 26, fill="#1e293b", outline="")
            c.create_rectangle(0, y + 20, (w - 4) * score / 100, y + 26, fill=ACCENT, outline="")


class ReportsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text="Reports", bg=BG, fg="white",
                 font=(FONT, 22, "bold")).pack(side="left")
        make_button(header, "Export CSV", self.export_csv, "primary").pack(side="right")
        panel = make_panel(self, "Class performance summary")
        panel.pack(fill="both", expand=True)
        self.text = tk.Label(panel, text="", bg=PANEL, fg=TEXT, justify="left",
                             anchor="nw", font=("Consolas", 11))
        self.text.pack(fill="both", expand=True, padx=20, pady=16)

    def refresh(self):
        students = get_students()
        summary = get_summary()
        if not students:
            self.text.config(text="No student records yet.")
            return
        ranked = sorted(students, key=lambda s: s["total"], reverse=True)
        averages = get_subject_averages()
        best = max(averages, key=averages.get)
        weakest = min(averages, key=averages.get)
        lines = [
            f'Total students       : {summary["students"]}',
            f'Class average        : {summary["class_average"]}%',
            f'Pass rate (>= 40%)   : {summary["pass_rate"]}%',
            f'Highest total        : {ranked[0]["total"]}  ({ranked[0]["name"]})',
            f'Lowest total         : {ranked[-1]["total"]}  ({ranked[-1]["name"]})',
            "",
            f'Strongest subject    : {best.replace("_", " ").title()}  ({averages[best]})',
            f'Weakest subject      : {weakest.replace("_", " ").title()}  ({averages[weakest]})',
            "",
            "Subject averages:",
        ]
        for subject, key in zip(SUBJECTS, SUBJECT_KEYS):
            lines.append(f"   {subject:<18} {averages[key]}")
        self.text.config(text="\n".join(lines))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV file", "*.csv")],
                                            initialfile="examiq_report.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Student ID", "Name"] + SUBJECTS + ["Total", "Percentage", "Grade"])
            ranked = sorted(get_students(), key=lambda s: s["total"], reverse=True)
            for i, st in enumerate(ranked, 1):
                writer.writerow([i, st["student_code"], st["name"]] + st["scores"] +
                                [st["total"], st["percentage"], st["grade"]])
        messagebox.showinfo("ExamIQ", "Report exported successfully.")


# =====================================================================
#  Main window with sidebar
# =====================================================================
class ExamIQApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ExamIQ - Smart Examination & Performance Analyzer")
        self.geometry("1220x720")
        self.minsize(1050, 640)
        self.configure(bg=BG)
        self.setup_styles()

        sidebar = tk.Frame(self, bg=SIDEBAR, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        logo = tk.Frame(sidebar, bg=SIDEBAR)
        logo.pack(fill="x", padx=18, pady=(22, 26))
        tk.Label(logo, text="EQ", bg="#0c2433", fg=ACCENT, width=3,
                 font=(FONT, 14, "bold")).pack(side="left")
        names = tk.Frame(logo, bg=SIDEBAR)
        names.pack(side="left", padx=10)
        tk.Label(names, text="ExamIQ PRO", bg=SIDEBAR, fg="white",
                 font=(FONT, 13, "bold")).pack(anchor="w")
        tk.Label(names, text="Performance Analyzer", bg=SIDEBAR, fg=MUTED,
                 font=(FONT, 8)).pack(anchor="w")

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True, padx=26, pady=22)

        self.pages = {
            "dashboard": DashboardPage(self.content, self),
            "students": StudentsPage(self.content, self),
            "entry": EntryPage(self.content, self),
            "rankings": RankingsPage(self.content, self),
            "analysis": AnalysisPage(self.content, self),
            "reports": ReportsPage(self.content, self),
        }
        self.nav_buttons = {}
        for key, label in [("dashboard", "Dashboard"), ("students", "Students"),
                           ("entry", "Marks Entry"), ("rankings", "Rankings"),
                           ("analysis", "C++ Analysis"), ("reports", "Reports")]:
            button = tk.Label(sidebar, text="   " + label, bg=SIDEBAR, fg=MUTED, anchor="w",
                              font=(FONT, 11, "bold"), pady=10, cursor="hand2")
            button.pack(fill="x", padx=12, pady=2)
            button.bind("<Button-1>", lambda e, k=key: self.show(k))
            self.nav_buttons[key] = button

        tk.Label(sidebar, text="Python  |  C++  |  PL/SQL", bg=SIDEBAR, fg=MUTED,
                 font=(FONT, 8)).pack(side="bottom", pady=16)

        for page in self.pages.values():
            page.place(in_=self.content, x=0, y=0, relwidth=1, relheight=1)
        self.show("dashboard")

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=30, borderwidth=0, font=(FONT, 10))
        style.configure("Treeview.Heading", background="#111827", foreground=MUTED,
                        font=(FONT, 9, "bold"), borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", "#164e63")],
                  foreground=[("selected", "white")])
        style.configure("Vertical.TScrollbar", background="#1e293b", troughcolor=PANEL,
                        bordercolor=PANEL, arrowcolor=MUTED)

    def show(self, key):
        for name, button in self.nav_buttons.items():
            active = name == key
            button.config(bg="#0f2a3d" if active else SIDEBAR, fg=ACCENT if active else MUTED)
        page = self.pages[key]
        page.refresh()
        page.tkraise()

    def refresh_all(self):
        for page in self.pages.values():
            page.refresh()


if __name__ == "__main__":
    init_db()
    ExamIQApp().mainloop()

"""
Web server for the Student Performance Analysis System.

Flask connects the browser (HTML/CSS/JavaScript) to the same Python
functions used by the command-line version (student_performance.py).

    Browser  --fetch()-->  Flask routes (this file)  -->  student_performance.py
                                                               |
                                                         Pandas + students.csv
"""

import json
import os

# Run from this file's folder so students.csv is always found.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# The web version never opens chart windows, so tell the module not to show plots.
os.environ["NO_SHOW"] = "1"

from flask import Flask, jsonify, render_template, request, send_file

import student_performance as sp   # <- our existing Python logic

app = Flask(__name__)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def to_records(df):
    """DataFrame -> list of plain Python dicts (safe for JSON)."""
    return json.loads(df.to_json(orient="records"))


def error(message, status=400):
    return jsonify({"error": message}), status


def read_student(data, existing_id=None):
    """Validate JSON from the browser and return (record, error_message)."""
    record = {}

    if existing_id is None:
        try:
            sid = int(data.get("ID"))
        except (TypeError, ValueError):
            return None, "Student ID must be a whole number."
        if sid <= 0:
            return None, "Student ID must be greater than 0."
        record["ID"] = sid
    else:
        record["ID"] = existing_id

    name = str(data.get("Name", "")).strip()
    if not name:
        return None, "Enter the student's name."
    if len(name) > 60:
        return None, "Name must be 60 characters or fewer."
    record["Name"] = name

    for subject in sp.SUBJECTS:
        try:
            marks = float(data.get(subject))
        except (TypeError, ValueError):
            return None, f"Enter {subject} marks as a number."
        if not 0 <= marks <= sp.MAX_MARKS:
            return None, f"{subject} marks must be between 0 and {sp.MAX_MARKS}."
        record[subject] = marks
    return record, None


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ----------------------------------------------------------------------
# API: read data
# ----------------------------------------------------------------------
@app.get("/api/students")
def list_students():
    df = sp.load_data()
    results = sp.calculate_results(df)
    return jsonify({
        "students": to_records(results),
        "subjects": sp.SUBJECTS,
        "pass_marks": sp.PASS_MARKS,
        "max_marks": sp.MAX_MARKS,
    })


@app.get("/api/summary")
def summary():
    df = sp.load_data()
    grades = [g for _, g in sp.GRADE_SCALE]
    if df.empty:
        return jsonify({"count": 0, "grades": [{"grade": g, "count": 0} for g in grades], "subject_stats": []})

    results = sp.calculate_results(df)
    top = results.iloc[0]
    distribution = results["Grade"].value_counts().reindex(grades, fill_value=0)
    return jsonify({
        "count": int(len(results)),
        "average": round(float(results["Percentage"].mean()), 2),
        "pass_rate": round(float((results["Result"] == "Pass").mean() * 100), 1),
        "top": {"name": top["Name"], "percentage": float(top["Percentage"])},
        "grades": [{"grade": g, "count": int(n)} for g, n in distribution.items()],
        "subject_stats": to_records(sp.subject_statistics(df)),
    })


# ----------------------------------------------------------------------
# API: change data
# ----------------------------------------------------------------------
@app.post("/api/students")
def add_student():
    df = sp.load_data()
    record, problem = read_student(request.get_json(silent=True) or {})
    if problem:
        return error(problem)
    if record["ID"] in df["ID"].values:
        return error(f"Student ID {record['ID']} already exists. Use a different ID.", 409)

    import pandas as pd
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    sp.save_data(df)
    return jsonify({"ok": True}), 201


@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    df = sp.load_data()
    if student_id not in df["ID"].values:
        return error("Student not found.", 404)

    record, problem = read_student(request.get_json(silent=True) or {}, existing_id=student_id)
    if problem:
        return error(problem)

    idx = df.index[df["ID"] == student_id][0]
    for column in ["Name"] + sp.SUBJECTS:
        df.at[idx, column] = record[column]
    sp.save_data(df)
    return jsonify({"ok": True})


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    df = sp.load_data()
    if student_id not in df["ID"].values:
        return error("Student not found.", 404)
    df = df[df["ID"] != student_id].reset_index(drop=True)
    sp.save_data(df)
    return jsonify({"ok": True})


# ----------------------------------------------------------------------
# API: report download
# ----------------------------------------------------------------------
@app.get("/api/report")
def report():
    df = sp.load_data()
    if df.empty:
        return error("There are no students to include in a report.")
    sp.export_report(df)                      # writes performance_report.txt
    return send_file(os.path.join(BASE_DIR, sp.REPORT_FILE), as_attachment=True)


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True)

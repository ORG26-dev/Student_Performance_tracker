"""
Student Performance Analysis System
-----------------------------------
A menu-driven Python application to manage student records and analyse
academic performance.

Features
  * Add / search / update / delete student records (stored in a CSV file)
  * Automatic total, percentage, grade and class rank
  * Subject-wise statistics (average, highest, lowest, topper, pass %)
  * Performance charts (Matplotlib) saved in the 'charts' folder
  * Text report export

Tools: Python, functions, dictionaries, CSV, Pandas, Matplotlib
"""

import os
import pandas as pd
import matplotlib

# If there is no display (e.g. server), fall back to a non-GUI backend.
if os.environ.get("NO_SHOW") == "1":
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATA_FILE = "students.csv"
CHART_DIR = "charts"
REPORT_FILE = "performance_report.txt"
SUBJECTS = ["Maths", "Physics", "Chemistry", "English", "Computer"]
MAX_MARKS = 100          # maximum marks per subject
PASS_MARKS = 40          # minimum marks to pass a subject
BASE_COLUMNS = ["ID", "Name"] + SUBJECTS

# Grade boundaries: (minimum percentage, grade) - checked from top to bottom
GRADE_SCALE = [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (0, "F")]


# ----------------------------------------------------------------------
# Data handling
# ----------------------------------------------------------------------
def load_data():
    """Load student records from the CSV file (create empty table if missing)."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # keep only the expected columns, in order
        df = df.reindex(columns=BASE_COLUMNS)
    else:
        df = pd.DataFrame(columns=BASE_COLUMNS)
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
    for sub in SUBJECTS:
        df[sub] = pd.to_numeric(df[sub], errors="coerce")
    return df.dropna(subset=["ID"]).reset_index(drop=True)


def save_data(df):
    """Save only the raw columns (computed columns are rebuilt on demand)."""
    df[BASE_COLUMNS].to_csv(DATA_FILE, index=False)


def get_grade(percentage):
    """Return the letter grade for a percentage."""
    for limit, grade in GRADE_SCALE:
        if percentage >= limit:
            return grade
    return "F"


def calculate_results(df):
    """Return a copy of df with Total, Percentage, Grade, Result and Rank."""
    result = df.copy()
    if result.empty:
        for col in ["Total", "Percentage", "Grade", "Result", "Rank"]:
            result[col] = []
        return result
    result["Total"] = result[SUBJECTS].sum(axis=1)
    result["Percentage"] = (result["Total"] / (MAX_MARKS * len(SUBJECTS)) * 100).round(2)
    result["Grade"] = result["Percentage"].apply(get_grade)
    # A student passes only if every subject is >= PASS_MARKS
    result["Result"] = (result[SUBJECTS] >= PASS_MARKS).all(axis=1).map(
        {True: "Pass", False: "Fail"})
    result["Rank"] = result["Total"].rank(method="min", ascending=False).astype(int)
    return result.sort_values("Rank").reset_index(drop=True)


# ----------------------------------------------------------------------
# Input helpers (validation)
# ----------------------------------------------------------------------
def ask_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("  ! Please enter a whole number.")


def ask_marks(subject):
    while True:
        try:
            marks = float(input(f"  {subject} marks (0-{MAX_MARKS}): ").strip())
            if 0 <= marks <= MAX_MARKS:
                return marks
            print(f"  ! Marks must be between 0 and {MAX_MARKS}.")
        except ValueError:
            print("  ! Please enter a number.")


def pause():
    input("\nPress Enter to continue...")


# ----------------------------------------------------------------------
# Record management
# ----------------------------------------------------------------------
def add_student(df):
    print("\n--- Add New Student ---")
    sid = ask_int("Student ID: ")
    if sid in df["ID"].values:
        print("  ! A student with this ID already exists.")
        return df
    name = input("Student name: ").strip()
    if not name:
        print("  ! Name cannot be empty.")
        return df
    record = {"ID": sid, "Name": name}
    for sub in SUBJECTS:
        record[sub] = ask_marks(sub)
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    save_data(df)
    print(f"  Student '{name}' added successfully.")
    return df


def search_student(df):
    print("\n--- Search Student ---")
    key = input("Enter student ID or part of the name: ").strip()
    if not key:
        return
    if key.isdigit():
        found = df[df["ID"] == int(key)]
    else:
        found = df[df["Name"].str.contains(key, case=False, na=False)]
    if found.empty:
        print("  No matching student found.")
        return
    results = calculate_results(df)
    print(results[results["ID"].isin(found["ID"])].to_string(index=False))


def update_student(df):
    print("\n--- Update Student Marks ---")
    sid = ask_int("Enter student ID to update: ")
    if sid not in df["ID"].values:
        print("  ! Student not found.")
        return df
    idx = df.index[df["ID"] == sid][0]
    print(f"Updating '{df.at[idx, 'Name']}'. Press Enter to keep the old marks.")
    for sub in SUBJECTS:
        while True:
            raw = input(f"  {sub} [{df.at[idx, sub]}]: ").strip()
            if raw == "":
                break
            try:
                value = float(raw)
                if 0 <= value <= MAX_MARKS:
                    df.at[idx, sub] = value
                    break
                print(f"  ! Marks must be between 0 and {MAX_MARKS}.")
            except ValueError:
                print("  ! Please enter a number.")
    save_data(df)
    print("  Record updated.")
    return df


def delete_student(df):
    print("\n--- Delete Student ---")
    sid = ask_int("Enter student ID to delete: ")
    if sid not in df["ID"].values:
        print("  ! Student not found.")
        return df
    confirm = input("Are you sure? (y/n): ").strip().lower()
    if confirm == "y":
        df = df[df["ID"] != sid].reset_index(drop=True)
        save_data(df)
        print("  Record deleted.")
    return df


# ----------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------
def show_all(df):
    print("\n--- All Students (sorted by rank) ---")
    if df.empty:
        print("  No records yet.")
        return
    print(calculate_results(df).to_string(index=False))


def show_rankings(df, top_n=5):
    print(f"\n--- Top {top_n} Students ---")
    if df.empty:
        print("  No records yet.")
        return
    res = calculate_results(df)
    print(res[["Rank", "ID", "Name", "Total", "Percentage", "Grade"]]
          .head(top_n).to_string(index=False))


def subject_statistics(df):
    """Return a DataFrame with statistics for every subject."""
    rows = []
    for sub in SUBJECTS:
        col = df[sub]
        rows.append({
            "Subject": sub,
            "Average": round(col.mean(), 2),
            "Highest": col.max(),
            "Lowest": col.min(),
            "Topper": df.loc[col.idxmax(), "Name"],
            "Pass %": round((col >= PASS_MARKS).mean() * 100, 1),
        })
    return pd.DataFrame(rows)


def show_subject_analysis(df):
    print("\n--- Subject-wise Analysis ---")
    if df.empty:
        print("  No records yet.")
        return
    stats = subject_statistics(df)
    print(stats.to_string(index=False))
    print(f"\nStrongest subject (highest average): {stats.loc[stats['Average'].idxmax(), 'Subject']}")
    print(f"Weakest subject   (lowest average) : {stats.loc[stats['Average'].idxmin(), 'Subject']}")


def show_class_summary(df):
    print("\n--- Class Summary ---")
    if df.empty:
        print("  No records yet.")
        return
    res = calculate_results(df)
    print(f"Total students      : {len(res)}")
    print(f"Class average (%)   : {res['Percentage'].mean():.2f}")
    print(f"Highest percentage  : {res['Percentage'].max():.2f} ({res.iloc[0]['Name']})")
    print(f"Lowest percentage   : {res['Percentage'].min():.2f} ({res.iloc[-1]['Name']})")
    print(f"Pass percentage     : {(res['Result'] == 'Pass').mean() * 100:.1f}%")
    print("\nGrade distribution:")
    print(res["Grade"].value_counts().reindex([g for _, g in GRADE_SCALE], fill_value=0).to_string())
    weak = res[res["Result"] == "Fail"]
    if not weak.empty:
        print("\nStudents needing attention (failed at least one subject):")
        print(", ".join(weak["Name"]))


# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------
def _finish_chart(filename):
    os.makedirs(CHART_DIR, exist_ok=True)
    path = os.path.join(CHART_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    print(f"  Chart saved: {path}")
    if os.environ.get("NO_SHOW") != "1":
        plt.show()
    plt.close()


def chart_subject_averages(df):
    stats = subject_statistics(df)
    plt.figure(figsize=(8, 5))
    bars = plt.bar(stats["Subject"], stats["Average"], color="#4C78A8")
    plt.bar_label(bars, fmt="%.1f")
    plt.title("Subject-wise Class Average")
    plt.ylabel("Average marks")
    plt.ylim(0, MAX_MARKS)
    _finish_chart("subject_averages.png")


def chart_grade_distribution(df):
    res = calculate_results(df)
    counts = res["Grade"].value_counts().reindex([g for _, g in GRADE_SCALE], fill_value=0)
    plt.figure(figsize=(8, 5))
    bars = plt.bar(counts.index, counts.values, color="#59A14F")
    plt.bar_label(bars)
    plt.title("Grade Distribution")
    plt.xlabel("Grade")
    plt.ylabel("Number of students")
    _finish_chart("grade_distribution.png")


def chart_top_students(df, top_n=5):
    res = calculate_results(df).head(top_n)
    plt.figure(figsize=(8, 5))
    bars = plt.barh(res["Name"][::-1], res["Percentage"][::-1], color="#F28E2B")
    plt.bar_label(bars, fmt="%.1f%%")
    plt.title(f"Top {top_n} Students by Percentage")
    plt.xlabel("Percentage")
    plt.xlim(0, 100)
    _finish_chart("top_students.png")


def chart_percentage_histogram(df):
    res = calculate_results(df)
    plt.figure(figsize=(8, 5))
    plt.hist(res["Percentage"], bins=range(0, 101, 10), color="#B07AA1", edgecolor="black")
    plt.title("Distribution of Student Percentages")
    plt.xlabel("Percentage")
    plt.ylabel("Number of students")
    _finish_chart("percentage_histogram.png")


def chart_student_vs_class(df):
    sid = ask_int("Enter student ID: ")
    if sid not in df["ID"].values:
        print("  ! Student not found.")
        return
    row = df[df["ID"] == sid].iloc[0]
    x = range(len(SUBJECTS))
    width = 0.38
    plt.figure(figsize=(9, 5))
    plt.bar([i - width / 2 for i in x], [row[s] for s in SUBJECTS], width,
            label=row["Name"], color="#4C78A8")
    plt.bar([i + width / 2 for i in x], [df[s].mean() for s in SUBJECTS], width,
            label="Class average", color="#BAB0AC")
    plt.xticks(list(x), SUBJECTS)
    plt.ylim(0, MAX_MARKS)
    plt.ylabel("Marks")
    plt.title(f"{row['Name']} vs Class Average")
    plt.legend()
    _finish_chart(f"student_{sid}_vs_class.png")


def chart_menu(df):
    if df.empty:
        print("  No records yet.")
        return
    while True:
        print("\n--- Charts ---")
        print("1. Subject-wise average")
        print("2. Grade distribution")
        print("3. Top 5 students")
        print("4. Percentage histogram")
        print("5. Student vs class average")
        print("6. Generate ALL class charts")
        print("0. Back")
        choice = input("Choose: ").strip()
        if choice == "1":
            chart_subject_averages(df)
        elif choice == "2":
            chart_grade_distribution(df)
        elif choice == "3":
            chart_top_students(df)
        elif choice == "4":
            chart_percentage_histogram(df)
        elif choice == "5":
            chart_student_vs_class(df)
        elif choice == "6":
            chart_subject_averages(df)
            chart_grade_distribution(df)
            chart_top_students(df)
            chart_percentage_histogram(df)
        elif choice == "0":
            break
        else:
            print("  ! Invalid choice.")


# ----------------------------------------------------------------------
# Report export
# ----------------------------------------------------------------------
def export_report(df):
    if df.empty:
        print("  No records to export.")
        return
    res = calculate_results(df)
    stats = subject_statistics(df)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("STUDENT PERFORMANCE REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total students    : {len(res)}\n")
        f.write(f"Class average (%) : {res['Percentage'].mean():.2f}\n")
        f.write(f"Pass percentage   : {(res['Result'] == 'Pass').mean() * 100:.1f}%\n\n")
        f.write("RANK LIST\n" + "-" * 60 + "\n")
        f.write(res[["Rank", "ID", "Name", "Total", "Percentage", "Grade", "Result"]]
                .to_string(index=False) + "\n\n")
        f.write("SUBJECT STATISTICS\n" + "-" * 60 + "\n")
        f.write(stats.to_string(index=False) + "\n")
    print(f"  Report saved to {REPORT_FILE}")


# ----------------------------------------------------------------------
# Main menu
# ----------------------------------------------------------------------
MENU = """
==========================================
   STUDENT PERFORMANCE ANALYSIS SYSTEM
==========================================
 1. Add student
 2. Search student
 3. Update student marks
 4. Delete student
 5. View all students (with rank & grade)
 6. Top performers
 7. Subject-wise analysis
 8. Class summary
 9. Performance charts
10. Export report
 0. Exit
"""


def main():
    df = load_data()
    while True:
        print(MENU)
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            df = add_student(df)
        elif choice == "2":
            search_student(df)
        elif choice == "3":
            df = update_student(df)
        elif choice == "4":
            df = delete_student(df)
        elif choice == "5":
            show_all(df)
        elif choice == "6":
            show_rankings(df)
        elif choice == "7":
            show_subject_analysis(df)
        elif choice == "8":
            show_class_summary(df)
        elif choice == "9":
            chart_menu(df)
        elif choice == "10":
            export_report(df)
        elif choice == "0":
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("  ! Invalid choice, try again.")
            continue
        if os.environ.get("NO_SHOW") != "1":
            pause()


if __name__ == "__main__":
    main()

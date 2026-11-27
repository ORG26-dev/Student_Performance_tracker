# 🎓 Student Performance Analysis System

A menu-driven Python application to manage student records and analyse academic performance. It calculates totals, percentages, grades and class ranks, produces subject-wise statistics, generates charts with Matplotlib, and exports a text report.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-data%20analysis-150458)
![Matplotlib](https://img.shields.io/badge/Matplotlib-charts-11557c)

## ✨ Features

- **Record management:** add, search, update and delete students (stored in `students.csv`, saved after every change)
- **Automatic results:** total, percentage, grade (A+ to F), pass/fail and class rank
- **Subject analysis:** average, highest, lowest, topper and pass % per subject, plus strongest/weakest subject
- **Class summary:** class average, highest/lowest scorer, pass percentage, grade distribution, students needing attention
- **Charts:** subject averages, grade distribution, top students, percentage histogram, student vs class average
- **Report export:** rank list and subject statistics saved to `performance_report.txt`
- **Input validation:** duplicate IDs, empty names and out-of-range marks are rejected

## 📊 Sample Output

| Subject Averages | Grade Distribution |
|:---:|:---:|
| ![Subject averages](subject_averages.png) | ![Grade distribution](grade_distribution.png) |

![Percentage histogram](percentage_histogram.png)

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or newer

### Installation
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# optional but recommended
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Run
```bash
python student_performance.py
```

On a machine without a display (e.g. a server), run with charts saved but not shown:
```bash
NO_SHOW=1 python student_performance.py          # Windows (PowerShell): $env:NO_SHOW=1
```

## 🖥️ Menu

```
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
```

## 📁 Project Structure

```
.
├── student_performance.py    # main program
├── students.csv              # sample data (15 students)
├── requirements.txt          # dependencies
├── performance_report.txt    # generated report
├── charts/                   # generated charts (created on first use)
└── *.png                     # sample chart images used in this README
```

## 📝 Data Format

`students.csv` must have these columns:

```csv
ID,Name,Maths,Physics,Chemistry,English,Computer
101,Aarav Sharma,92,88,85,78,95
```

Subjects, maximum marks and pass marks can be changed in the configuration block at the top of `student_performance.py` (`SUBJECTS`, `MAX_MARKS`, `PASS_MARKS`).

## 🏆 Grading Scheme

| Percentage | Grade |
|-----------|-------|
| 90 and above | A+ |
| 80 – 89 | A |
| 70 – 79 | B |
| 60 – 69 | C |
| 50 – 59 | D |
| below 50 | F |

A student **passes only if they score at least 40 in every subject**. Ties in total marks share the same rank.

## ⚙️ How It Works

1. `load_data()` reads the CSV into a Pandas DataFrame.
2. `calculate_results()` adds Total, Percentage, Grade, Result and Rank columns.
3. Analysis functions use Pandas (`mean`, `max`, `idxmax`, `value_counts`) on the DataFrame.
4. Chart functions use Matplotlib and save PNG files.
5. Every add/update/delete is written back to the CSV immediately.

## 🛠️ Built With

Python · Pandas · Matplotlib · CSV

## 🔮 Future Improvements

- Tkinter / web GUI
- SQLite database instead of CSV
- Semester-wise tracking
- PDF report export

## 📄 License

This project is open source. Add a license of your choice (e.g. MIT) before publishing.

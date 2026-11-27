Student Performance Analysis System - Web Version
A browser dashboard for the Python project. Flask connects the web page to the same Python/Pandas code used by the command-line version.

Run it
pip install -r requirements.txt
python app.py
Then open http://127.0.0.1:5000 in your browser.

How Python is connected to the website
Browser (index.html + app.js)
      |  fetch("/api/students")          <- JavaScript asks for data
      v
Flask routes in app.py                   <- Python receives the request
      |  sp.load_data(), sp.calculate_results(), ...
      v
student_performance.py  +  Pandas  +  students.csv
      |
      v  JSON response -> JavaScript draws the table and charts
Route	Method	What it does
/	GET	Shows the web page
/api/students	GET	Returns all students with total, %, grade, result, rank
/api/summary	GET	Returns class average, pass rate, subject stats, grade counts
/api/students	POST	Adds a student (validated)
/api/students/<id>	PUT	Updates name and marks
/api/students/<id>	DELETE	Deletes a student
/api/report	GET	Downloads the text report
Files
app.py                  Flask server (the Python-to-web connection)
student_performance.py  Original logic (load_data, calculate_results, subject_statistics ...)
students.csv            Data file (changes made on the website are saved here)
templates/index.html    Page structure
static/style.css        Design
static/app.js           Browser logic (fetch calls, table, sorting, forms)
Features
Class register with heat-coloured marks, sorting and search
Subject averages, grade distribution and "needs attention" list
Student detail panel comparing marks with the class average
Add, edit and delete students with validation
Download report
Note: the page loads two fonts from Google Fonts. Without internet it falls back to system fonts and everything still works.

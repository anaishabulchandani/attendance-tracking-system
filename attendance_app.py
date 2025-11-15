import streamlit as st
from datetime import date
import pandas as pd
import json
from pathlib import Path

# Queue (FIFO)
class Queue:
    def __init__(self):
        self.q = []

    def enqueue(self, item):            
        self.q.append(item)

    def dequeue(self):                  
        return self.q.pop(0) if not self.is_empty() else None

    def is_empty(self):                 
        return len(self.q) == 0

    def get_all(self):                  
        return list(self.q)

# Stack (LIFO)
class Stack:
    def __init__(self):
        self.s = []

    def push(self, item):               
        self.s.append(item)

    def pop(self):                      
        return self.s.pop() if self.s else None

# Student Save/Load Handling
DATA_DIR = Path("data")
STUDENTS_FILE = DATA_DIR / "students.json"

def load_students():                    # Load students from JSON file
    if STUDENTS_FILE.exists():
        try:
            return json.loads(STUDENTS_FILE.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_students():                    # Save students dictionary to JSON file
    DATA_DIR.mkdir(exist_ok=True)
    STUDENTS_FILE.write_text(json.dumps(st.session_state.students, indent=2),
                             encoding="utf-8")

# Session State Initialization
if "students" not in st.session_state:
    st.session_state.students = load_students()

if "attendance" not in st.session_state:
    st.session_state.attendance = {}

if "queue" not in st.session_state:
    st.session_state.queue = Queue()

if "stack" not in st.session_state:
    st.session_state.stack = Stack()

# Functions
def add_student(roll, name):            # Add a student to the student list
    if roll in st.session_state.students:
        st.warning("Roll already exists.")
        return
    st.session_state.students[roll] = name
    save_students()
    st.success("Student added")

def delete_student(roll):               # Delete student and remove from attendance
    if roll in st.session_state.students:
        del st.session_state.students[roll]
        for d in st.session_state.attendance:
            st.session_state.attendance[d].pop(roll, None)
        save_students()
        st.success("Student deleted")

def mark_attendance(roll, d, status):   # Mark attendance directly for a student
    st.session_state.attendance.setdefault(d, {})
    prev = st.session_state.attendance[d].get(roll)
    st.session_state.stack.push((roll, d, prev))
    st.session_state.attendance[d][roll] = status
    st.success("Attendance marked")

def delete_attendance_date(d):          # Delete all attendance for selected date
    if d in st.session_state.attendance:
        del st.session_state.attendance[d]
        st.success("Attendance deleted")

def queue_add(roll, d, status):         # Add attendance request to queue
    st.session_state.queue.enqueue({"roll": roll, "date": d, "status": status})
    st.success("Added to queue")

def queue_process_next():               # Process and mark the next queued task
    item = st.session_state.queue.dequeue()
    if not item:
        st.warning("Queue empty")
        return

    roll, d, status = item["roll"], item["date"], item["status"]
    st.session_state.attendance.setdefault(d, {})
    prev = st.session_state.attendance[d].get(roll)
    st.session_state.stack.push((roll, d, prev))
    st.session_state.attendance[d][roll] = status
    st.success(f"Processed: {roll} marked {status}")

def student_report(roll):               # Generate student-wise attendance report
    return [{"Date": d, "Status": data.get(roll, "Absent")}
            for d, data in st.session_state.attendance.items()]

def daily_present_counts():             # Count number of present students per day
    return [{"Date": d, "Present": sum(1 for s in data.values() if s == "Present")}
            for d, data in st.session_state.attendance.items()]

# Streamlit UI
st.set_page_config(page_title="Attendance System", layout="wide")
st.title("Attendance Tracking System")

tab1, tab2, tab3 = st.tabs(["Students", "Attendance", "Reports"])

# TAB 1: Students
with tab1:
    st.header("Add / Delete Students")
    col1, col2 = st.columns(2)
    roll = col1.text_input("Roll Number")
    name = col2.text_input("Name")

    if st.button("Add Student"):
        add_student(roll.strip(), name.strip())

    st.subheader("Current Students")
    if st.session_state.students:
        df = pd.DataFrame([{"Roll": r, "Name": n}
                           for r, n in st.session_state.students.items()])
        st.dataframe(df)

        del_roll = st.selectbox("Select Roll to Delete",
                                [""] + list(st.session_state.students.keys()))
        if st.button("Delete Student") and del_roll:
            delete_student(del_roll)
    else:
        st.info("No students added yet.")

# TAB 2: Attendance
with tab2:
    st.header("Mark Attendance")
    student_options = [f"{r} – {n}" for r, n in st.session_state.students.items()]

    colA, colB, colC = st.columns(3)
    sel_date = colA.date_input("Select Date", value=date.today()).isoformat()
    sel_student_option = colB.selectbox("Select Student", [""] + student_options)
    sel_roll = sel_student_option.split(" – ")[0] if sel_student_option else ""
    sel_status = colC.selectbox("Status", ["Present", "Absent"])

    if st.button("Mark Directly"):
        if not sel_roll:
            st.warning("Select a student")
        else:
            mark_attendance(sel_roll, sel_date, sel_status)

    st.markdown("### OR Add to Queue")
    q_student_option = st.selectbox("Queue: Select Student",
                                    [""] + student_options)
    q_roll = q_student_option.split(" – ")[0] if q_student_option else ""
    q_status = st.selectbox("Queue Status", ["Present", "Absent"])

    if st.button("Add to Queue"):
        if not q_roll:
            st.warning("Select a student")
        else:
            queue_add(q_roll, date.today().isoformat(), q_status)

    st.subheader("Pending Queue")
    st.table(st.session_state.queue.get_all())

    if st.button("Process Next Queue Item"):
        queue_process_next()

    st.subheader(f"Attendance on {sel_date}")
    day_data = st.session_state.attendance.get(sel_date, {})
    rows = [{"Roll": r, "Name": st.session_state.students.get(r, ""),
             "Status": s} for r, s in day_data.items()]

    if rows:
        st.table(rows)
        if st.button("Delete Attendance for This Date"):
            delete_attendance_date(sel_date)
    else:
        st.info("No attendance for this date.")

# TAB 3: Reports
with tab3:
    st.header("Reports")
    rep_roll = st.selectbox("Select Student",
                            [""] + list(st.session_state.students.keys()))

    if st.button("Show Report"):
        data = student_report(rep_roll)
        st.table(data if data else [])

    st.subheader("Date-wise Present Count")
    counts = daily_present_counts()
    if counts:
        st.bar_chart(pd.DataFrame(counts).set_index("Date"))
    else:
        st.info("No attendance yet.")

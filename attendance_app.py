import streamlit as st
from datetime import date
import pandas as pd


# Queue (FIFO)
class Queue:
    def __init__(self):
        self.q = []

    def enqueue(self, item):
        self.q.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.q.pop(0)
        return None

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
        if self.s:
            return self.s.pop()
        return None


if "students" not in st.session_state:
    st.session_state.students = {}       # {roll: name}

if "attendance" not in st.session_state:
    st.session_state.attendance = {}     # {date: {roll: Present/Absent}}

if "queue" not in st.session_state:
    st.session_state.queue = Queue()

if "stack" not in st.session_state:
    st.session_state.stack = Stack()



def add_student(roll, name):
    if roll in st.session_state.students:
        st.warning("Roll already exists.")
        return
    st.session_state.students[roll] = name
    st.success("Student added")

def delete_student(roll):
    if roll in st.session_state.students:
        del st.session_state.students[roll]
        for d in st.session_state.attendance:
            st.session_state.attendance[d].pop(roll, None)
        st.success("Student deleted")

def mark_attendance(roll, d, status):
    if d not in st.session_state.attendance:
        st.session_state.attendance[d] = {}

    prev = st.session_state.attendance[d].get(roll)
    st.session_state.stack.push((roll, d, prev))  # track last action

    st.session_state.attendance[d][roll] = status
    st.success("Attendance marked")

def delete_attendance_date(d):
    if d in st.session_state.attendance:
        del st.session_state.attendance[d]
        st.success("Attendance deleted")

def queue_add(roll, d, status):
    st.session_state.queue.enqueue({"roll": roll, "date": d, "status": status})
    st.success("Added to queue")

def queue_process_next():
    item = st.session_state.queue.dequeue()
    if not item:
        st.warning("Queue empty")
        return

    roll = item["roll"]
    d = item["date"]
    status = item["status"]

    if d not in st.session_state.attendance:
        st.session_state.attendance[d] = {}

    prev = st.session_state.attendance[d].get(roll)
    st.session_state.stack.push((roll, d, prev))

    st.session_state.attendance[d][roll] = status
    st.success(f"Processed: {roll} marked {status}")


def student_report(roll):
    rows = []
    for d, data in st.session_state.attendance.items():
        status = data.get(roll, "Absent")
        rows.append({"Date": d, "Status": status})
    return rows

def daily_present_counts():
    rows = []
    for d, data in st.session_state.attendance.items():
        present_count = sum(1 for s in data.values() if s == "Present")
        rows.append({"Date": d, "Present": present_count})
    return rows



# STREAMLIT UI

st.set_page_config(page_title="Attendance System", layout="wide")
st.title("Attendance Tracking System (Simple DSA Version)")

tab1, tab2, tab3 = st.tabs(["Students", "Attendance", "Reports"])



# TAB 1: STUDENTS

with tab1:
    st.header("Add / Delete Students")

    col1, col2 = st.columns(2)
    with col1:
        roll = st.text_input("Roll Number")
    with col2:
        name = st.text_input("Name")

    if st.button("Add Student"):
        add_student(roll.strip(), name.strip())

    st.subheader("Current Students")

    if st.session_state.students:
        df = pd.DataFrame(
            [{"Roll": r, "Name": n} for r, n in st.session_state.students.items()]
        )
        st.dataframe(df)

        del_roll = st.selectbox("Select Roll to Delete", [""] + list(st.session_state.students.keys()))
        if st.button("Delete Student"):
            if del_roll:
                delete_student(del_roll)
    else:
        st.info("No students added yet.")



# TAB 2: ATTENDANCE

with tab2:
    st.header("Mark Attendance")

    colA, colB, colC = st.columns(3)
    with colA:
        sel_date = st.date_input("Select Date", value=date.today()).isoformat()
    with colB:
        sel_roll = st.selectbox("Select Student Roll", [""] + list(st.session_state.students.keys()))
    with colC:
        sel_status = st.selectbox("Status", ["Present", "Absent"])

    if st.button("Mark Directly"):
        if not sel_roll:
            st.warning("Select a student")
        else:
            mark_attendance(sel_roll, sel_date, sel_status)

    st.subheader("OR Add request to Queue")

    q_roll = st.text_input("Queue Roll")
    q_status = st.selectbox("Queue Status", ["Present", "Absent"])
    if st.button("Add to Queue"):
        queue_add(q_roll.strip(), date.today().isoformat(), q_status)

    st.subheader("Pending Queue")
    q_items = st.session_state.queue.get_all()
    st.table(q_items)

    if st.button("Process Next Queue Item"):
        queue_process_next()

    st.subheader(f"Attendance on {sel_date}")
    rows = []
    if sel_date in st.session_state.attendance:
        for r, s in st.session_state.attendance[sel_date].items():
            rows.append({"Roll": r, "Name": st.session_state.students.get(r, ""), "Status": s})
        st.table(rows)

        if st.button("Delete Attendance for This Date"):
            delete_attendance_date(sel_date)
    else:
        st.info("No attendance for this date.")


# TAB 3: REPORTS

with tab3:
    st.header("Reports")

    st.subheader("Student Report")
    rep_roll = st.selectbox("Select Student", [""] + list(st.session_state.students.keys()))

    if st.button("Show Report"):
        data = student_report(rep_roll)
        if data:
            st.table(data)
        else:
            st.info("No attendance records.")

    st.subheader("Date-wise Present Count")
    counts = daily_present_counts()
    if counts:
        df_counts = pd.DataFrame(counts).set_index("Date")
        st.bar_chart(df_counts)
    else:
        st.info("No attendance yet.")


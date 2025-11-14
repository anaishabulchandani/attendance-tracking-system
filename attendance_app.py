import streamlit as st
from datetime import date

if "students" not in st.session_state or not isinstance(st.session_state.students, dict):
    st.session_state.students = {}

# Queue (FIFO)
class Queue:
    def __init__(self):
        self.q = []

    def enqueue(self, item):
        self.q.append(item)

    def dequeue(self):
        if self.is_empty():
            return None
        return self.q.pop(0)

    def is_empty(self):
        return len(self.q)

    def get_all(self):
        return self.q


# Stack (LIFO for Undo)
class Stack:
    def __init__(self):
        self.s = []

    def push(self, item):
        self.s.append(item)

    def pop(self):
        if self.is_empty():
            return None
        return self.s.pop()

    def is_empty(self):
        return len(self.s) == 0


# Linked List (Log History)
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None

    def insert(self, data):
        node = Node(data)
        if self.head is None:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node

    def get_all(self):
        logs = []
        cur = self.head
        while cur:
            logs.append(cur.data)
            cur = cur.next
        return logs


# STREAMLIT SESSION INITIALIZATION

if "students" not in st.session_state:
    st.session_state.students = {}  # { id: name }

if "attendance" not in st.session_state:
    st.session_state.attendance = {}  # { date : [ids] }

if "log_queue" not in st.session_state:
    st.session_state.log_queue = Queue()

if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = Stack()

if "log_history" not in st.session_state:
    st.session_state.log_history = LinkedList()


# STREAMLIT UI 

st.title("Attendance Tracking System")

tab1, tab2, tab3, tab4 = st.tabs([
    "Add Student",
    "Mark Attendance",
    "Queue & Undo",
    "Reports"
])

# TAB 1 — Add Student

with tab1:
    st.header("Add Student")

    col1, col2 = st.columns(2)
    with col1:
        new_id = st.text_input("Student ID")
    with col2:
        new_name = st.text_input("Student Name")

    if st.button("Add Student"):
        if new_id in st.session_state.students:
            st.warning("Student ID already exists")
        else:
            st.session_state.students[new_id] = new_name
            st.success("Student added successfully")

    if st.session_state.students:
        st.subheader("Student List")
        st.table(
            [{"ID": sid, "Name": name}
             for sid, name in st.session_state.students.items()]
        )

# TAB 2 — Mark Attendance

with tab2:
    st.header("Mark Attendance Manually")

    sid = st.text_input("Enter Student ID")
    d = st.date_input("Select Date", value=date.today()).isoformat()

    if st.button("Mark Present"):
        if d not in st.session_state.attendance:
            st.session_state.attendance[d] = []

        if sid not in st.session_state.attendance[d]:
            st.session_state.attendance[d].append(sid)

            # Save for undo
            st.session_state.undo_stack.push(("unmark", sid, d))

            # Add to log history
            st.session_state.log_history.insert(
                {"sid": sid, "date": d, "type": "manual"}
            )

            st.success("Attendance marked")
        else:
            st.warning("Already marked present")


# TAB 3 — Queue + Undo

with tab3:

    st.header("Add to Attendance Queue")

    q_sid = st.text_input("Queue - Student ID")

    if st.button("Add to Queue"):
        entry = {"sid": q_sid, "date": date.today().isoformat()}
        st.session_state.log_queue.enqueue(entry)
        st.session_state.log_history.insert({"sid": q_sid, "date": entry["date"], "type": "queued"})
        st.success("Added to Queue")

    st.subheader("Pending Queue")
    st.table(st.session_state.log_queue.get_all())

    st.header("Process Queue")
    if st.button("Process Next"):
        log = st.session_state.log_queue.dequeue()
        if log:
            sid = log["sid"]
            dd = log["date"]

            if dd not in st.session_state.attendance:
                st.session_state.attendance[dd] = []

            if sid not in st.session_state.attendance[dd]:
                st.session_state.attendance[dd].append(sid)

                st.session_state.undo_stack.push(("unmark", sid, dd))
                st.session_state.log_history.insert({"sid": sid, "date": dd, "type": "queue-processed"})

                st.success(f"Processed {sid}")
        else:
            st.warning("Queue is empty")

    st.header("Undo Last Action")

    if st.button("Undo"):
        last = st.session_state.undo_stack.pop()
        if last is None:
            st.warning("Nothing to undo")
        else:
            action, sid, dd = last
            if action == "unmark":
                if dd in st.session_state.attendance and sid in st.session_state.attendance[dd]:
                    st.session_state.attendance[dd].remove(sid)
                    st.success("Undo successful")

    st.header("Log History (Linked List)")
    st.table(st.session_state.log_history.get_all())


# TAB 4 — Reports

with tab4:
    st.header("Attendance Reports")

    
    st.subheader("Student Attendance Report")

    student = st.text_input("Enter Student ID for Report")

    if st.button("Show Student Report"):
        result = []
        for d, ids in st.session_state.attendance.items():
            if student in ids:
                result.append({"Date": d, "Status": "Present"})

        if result:
            st.table(result)
        else:
            st.warning("No attendance found for this student")


    st.subheader("Daily Summary")

    dd = st.date_input("Choose Date", value=date.today()).isoformat()

    if st.button("Show Daily Summary"):
        if dd in st.session_state.attendance:
            present_ids = st.session_state.attendance[dd]
            data = [{"Student ID": i, "Name": st.session_state.students.get(i, "Unknown")}
                    for i in present_ids]
            st.table(data)
        else:
            st.warning("No records for this date")


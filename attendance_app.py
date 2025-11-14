import streamlit as st
from datetime import date

# Queue (using list)
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
        return len(self.q) == 0

    def get_all(self):
        return self.q


# Stack (Undo)
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
        newnode = Node(data)
        if self.head is None:
            self.head = newnode
        else:
            temp = self.head
            while temp.next:
                temp = temp.next
            temp.next = newnode

    def get_all(self):
        logs = []
        temp = self.head
        while temp:
            logs.append(temp.data)
            temp = temp.next
        return logs


# Initialize session state
if "students" not in st.session_state:
    st.session_state.students = []  # simple list storing student IDs

if "attendance" not in st.session_state:
    st.session_state.attendance = {}  # date -> list of SIDs

if "log_queue" not in st.session_state:
    st.session_state.log_queue = Queue()

if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = Stack()

if "log_history" not in st.session_state:
    st.session_state.log_history = LinkedList()


# Streamlit UI
st.title("Attendance Tracking System")


# Add Student
st.header("Add Student")
sid = st.text_input("Enter Student ID")

if st.button("Add Student"):
    if sid in st.session_state.students:
        st.warning("Student already exists")
    else:
        st.session_state.students.append(sid)
        st.success("Student added")


# Mark Attendance Manually
st.header("Mark Attendance Manually")

sel_sid = st.text_input("Student ID for attendance")
sel_date = st.date_input("Select Date", value=date.today())

if st.button("Mark Present"):
    ds = sel_date.isoformat()

    if ds not in st.session_state.attendance:
        st.session_state.attendance[ds] = []

    if sel_sid not in st.session_state.attendance[ds]:
        st.session_state.attendance[ds].append(sel_sid)

        st.session_state.undo_stack.push(("unmark", sel_sid, ds))

        st.success("Attendance marked")
    else:
        st.warning("Already marked present")


# Add Swipe Log (Queue)
st.header("Add Swipe Log (Queue)")

log_sid = st.text_input("Swipe Log - Student ID")

if st.button("Add Log Entry"):
    entry = {"sid": log_sid, "date": date.today().isoformat()}

    st.session_state.log_queue.enqueue(entry)
    st.session_state.log_history.insert(entry)

    st.success("Log added to queue")


# Process Next Log
if st.button("Process Next Log"):
    log = st.session_state.log_queue.dequeue()

    if log:
        ds = log["date"]
        sid = log["sid"]

        if ds not in st.session_state.attendance:
            st.session_state.attendance[ds] = []

        if sid not in st.session_state.attendance[ds]:

            st.session_state.attendance[ds].append(sid)
            st.session_state.undo_stack.push(("unmark", sid, ds))

        st.success(f"Processed Log: {log}")
    else:
        st.warning("No logs in queue")


# Undo Last Action (Stack)
st.header("Undo Last Action")

if st.button("Undo"):
    last = st.session_state.undo_stack.pop()

    if last is None:
        st.warning("Nothing to undo")
    else:
        action, sid, ds = last

        if action == "unmark":
            if ds in st.session_state.attendance:
                if sid in st.session_state.attendance[ds]:
                    st.session_state.attendance[ds].remove(sid)
                    st.success("Undo successful")


# Display Attendance
st.header("Attendance Records")
st.write(st.session_state.attendance)


# Display Queue
st.header("Pending Log Queue")
st.write(st.session_state.log_queue.get_all())


# Display Linked List Log History
st.header("Complete Log History (Linked List)")
st.write(st.session_state.log_history.get_all())

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("library.db", check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            year INTEGER,
            status TEXT DEFAULT 'Available'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS issued (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            issued_to TEXT,
            issue_date TEXT,
            return_date TEXT
        )
    """)
    conn.commit()

create_tables()

# -----------------------------
# DB FUNCTIONS
# -----------------------------
def add_book(title, author, year):
    c.execute("INSERT INTO books (title, author, year, status) VALUES (?, ?, ?, 'Available')",
              (title, author, year))
    conn.commit()

def get_books():
    return pd.read_sql_query("SELECT * FROM books", conn)

def delete_book(book_id):
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()

def issue_book(book_id, issued_to):
    c.execute("SELECT status FROM books WHERE id=?", (book_id,))
    status = c.fetchone()

    if status and status[0] == "Available":
        c.execute("UPDATE books SET status='Issued' WHERE id=?", (book_id,))
        c.execute("""
            INSERT INTO issued (book_id, issued_to, issue_date, return_date)
            VALUES (?, ?, ?, ?)
        """, (book_id, issued_to, str(datetime.now()), None))
        conn.commit()
        return True
    return False

def return_book(book_id):
    c.execute("SELECT id FROM issued WHERE book_id=? AND return_date IS NULL", (book_id,))
    record = c.fetchone()

    if record:
        c.execute("UPDATE books SET status='Available' WHERE id=?", (book_id,))
        c.execute("""
            UPDATE issued SET return_date=? WHERE book_id=? AND return_date IS NULL
        """, (str(datetime.now()), book_id))
        conn.commit()
        return True
    return False

def get_issued():
    return pd.read_sql_query("SELECT * FROM issued", conn)

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Library Management System", layout="wide")

st.title("📚 Library Management System")

menu = ["Home", "Add Book", "View Books", "Issue Book", "Return Book", "Delete Book", "Issued Records"]
choice = st.sidebar.selectbox("Navigation", menu)

# -----------------------------
# HOME
# -----------------------------
if choice == "Home":
    st.subheader("Welcome to Library Management System")
    st.write("Manage books, issue/return records using SQLite + Streamlit.")
    
    df = get_books()
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Books", len(df))
    col2.metric("Available", len(df[df["status"] == "Available"]))
    col3.metric("Issued", len(df[df["status"] == "Issued"]))

    st.dataframe(df, use_container_width=True)

# -----------------------------
# ADD BOOK
# -----------------------------
elif choice == "Add Book":
    st.subheader("➕ Add New Book")

    title = st.text_input("Book Title")
    author = st.text_input("Author")
    year = st.number_input("Publication Year", min_value=0, step=1)

    if st.button("Add Book"):
        if title and author:
            add_book(title, author, int(year))
            st.success("Book added successfully!")
        else:
            st.error("Please fill all fields")

# -----------------------------
# VIEW BOOKS
# -----------------------------
elif choice == "View Books":
    st.subheader("📖 Book List")
    df = get_books()
    st.dataframe(df, use_container_width=True)

# -----------------------------
# ISSUE BOOK
# -----------------------------
elif choice == "Issue Book":
    st.subheader("📤 Issue Book")

    df = get_books()
    available_books = df[df["status"] == "Available"]

    book_id = st.selectbox("Select Book ID", available_books["id"].tolist() if not available_books.empty else [])
    issued_to = st.text_input("Issue To (Name)")

    if st.button("Issue"):
        if book_id and issued_to:
            if issue_book(book_id, issued_to):
                st.success("Book issued successfully!")
            else:
                st.error("Book is not available")

# -----------------------------
# RETURN BOOK
# -----------------------------
elif choice == "Return Book":
    st.subheader("📥 Return Book")

    df = get_books()
    issued_books = df[df["status"] == "Issued"]

    book_id = st.selectbox("Select Book ID", issued_books["id"].tolist() if not issued_books.empty else [])

    if st.button("Return"):
        if return_book(book_id):
            st.success("Book returned successfully!")
        else:
            st.error("Invalid operation")

# -----------------------------
# DELETE BOOK
# -----------------------------
elif choice == "Delete Book":
    st.subheader("🗑 Delete Book")

    df = get_books()
    book_id = st.selectbox("Select Book ID", df["id"].tolist())

    if st.button("Delete"):
        delete_book(book_id)
        st.success("Book deleted successfully!")

# -----------------------------
# ISSUED RECORDS
# -----------------------------
elif choice == "Issued Records":
    st.subheader("📜 Issued Book Records")
    df = get_issued()
    st.dataframe(df, use_container_width=True)

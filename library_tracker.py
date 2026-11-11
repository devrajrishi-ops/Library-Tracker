"""Library Book Tracker - CLI + SQLite (no external libraries needed)."""
import sqlite3
from datetime import date, timedelta

DB = "library.db"
LOAN_DAYS = 14
FINE_PER_DAY = 2  # rupees


def connect():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        issued_to TEXT,
        due_date TEXT)""")
    return con


def add_book(con):
    title = input("Book title: ").strip()
    author = input("Author: ").strip()
    if not title or not author:
        print("Title aur author dono chahiye.")
        return
    con.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    con.commit()
    print("Book add ho gayi.")


def list_books(con, rows=None):
    rows = rows if rows is not None else con.execute("SELECT * FROM books").fetchall()
    if not rows:
        print("Kuch nahi mila.")
        return
    print(f"{'ID':<4}{'Title':<28}{'Author':<20}{'Status'}")
    for id_, title, author, to, due in rows:
        status = f"Issued to {to} (due {due})" if to else "Available"
        print(f"{id_:<4}{title[:26]:<28}{author[:18]:<20}{status}")


def search(con):
    q = f"%{input('Search (title/author): ').strip()}%"
    rows = con.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?", (q, q)).fetchall()
    list_books(con, rows)


def issue(con):
    book_id = input("Book ID: ").strip()
    row = con.execute("SELECT issued_to FROM books WHERE id=?", (book_id,)).fetchone()
    if not row:
        print("Aisi book nahi hai.")
    elif row[0]:
        print("Ye book already issued hai.")
    else:
        name = input("Student name: ").strip()
        due = (date.today() + timedelta(days=LOAN_DAYS)).isoformat()
        con.execute("UPDATE books SET issued_to=?, due_date=? WHERE id=?",
                    (name, due, book_id))
        con.commit()
        print(f"Issued to {name}. Due date: {due}")


def return_book(con):
    book_id = input("Book ID: ").strip()
    row = con.execute("SELECT issued_to, due_date FROM books WHERE id=?",
                      (book_id,)).fetchone()
    if not row or not row[0]:
        print("Ye book issued nahi hai.")
        return
    late = (date.today() - date.fromisoformat(row[1])).days
    if late > 0:
        print(f"Late by {late} days. Fine: Rs {late * FINE_PER_DAY}")
    con.execute("UPDATE books SET issued_to=NULL, due_date=NULL WHERE id=?", (book_id,))
    con.commit()
    print("Book return ho gayi.")


def overdue(con):
    today = date.today().isoformat()
    rows = con.execute(
        "SELECT * FROM books WHERE issued_to IS NOT NULL AND due_date < ?", (today,)).fetchall()
    list_books(con, rows)


MENU = {
    "1": ("Add book", add_book),
    "2": ("List all books", list_books),
    "3": ("Search", search),
    "4": ("Issue book", issue),
    "5": ("Return book", return_book),
    "6": ("Overdue books", overdue),
}


def main():
    con = connect()
    while True:
        print("\n=== Library Tracker ===")
        for k, (name, _) in MENU.items():
            print(f"{k}. {name}")
        print("0. Exit")
        choice = input("Choice: ").strip()
        if choice == "0":
            break
        if choice in MENU:
            MENU[choice][1](con)
        else:
            print("Galat choice.")
    con.close()


if __name__ == "__main__":
    main()

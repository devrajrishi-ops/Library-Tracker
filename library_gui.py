import os
import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, simpledialog, ttk

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "library.db")
LOAN_DAYS = 14
FINE_PER_DAY = 2  # rupees


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Tracker")
        self.geometry("860x540")
        self.minsize(720, 460)
        self.con = sqlite3.connect(DB)
        self.con.execute("""CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            issued_to TEXT,
            due_date TEXT)""")
        ttk.Style(self).theme_use("clam")
        self.build_ui()
        self.refresh()

    def build_ui(self):
        head = tk.Frame(self, bg="#1f3a5f")
        head.pack(fill="x")
        tk.Label(head, text="Library Tracker", bg="#1f3a5f", fg="white",
                 font=("Helvetica", 20, "bold")).pack(side="left", padx=16, pady=12)
        tk.Label(head, text="Developed by DevRishi", bg="#1f3a5f", fg="#cfd9e8").pack(side="right", padx=16)

        form = ttk.LabelFrame(self, text=" Add a new book ")
        form.pack(fill="x", padx=12, pady=(12, 6))
        self.title_var, self.author_var = tk.StringVar(), tk.StringVar()
        ttk.Label(form, text="Title").grid(row=0, column=0, padx=6, pady=8)
        ttk.Entry(form, textvariable=self.title_var, width=28).grid(row=0, column=1)
        ttk.Label(form, text="Author").grid(row=0, column=2, padx=6)
        ttk.Entry(form, textvariable=self.author_var, width=22).grid(row=0, column=3)
        ttk.Button(form, text="Add Book", command=self.add_book).grid(row=0, column=4, padx=10)

        bar = tk.Frame(self)
        bar.pack(fill="x", padx=12, pady=6)
        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())
        ttk.Entry(bar, textvariable=self.search_var, width=32).pack(side="left", padx=6)
        ttk.Button(bar, text="Show overdue", command=self.show_overdue).pack(side="left", padx=6)
        ttk.Button(bar, text="Show all", command=self.show_all).pack(side="left")

        cols = ("id", "title", "author", "status", "due")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, (50, 260, 180, 200, 110)):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("free", foreground="#1b7f3b")
        self.tree.tag_configure("out", foreground="#b36b00")
        self.tree.tag_configure("late", foreground="#c62828")
        self.tree.pack(fill="both", expand=True, padx=12, pady=6)

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=12, pady=(0, 6))
        ttk.Button(btns, text="Issue", command=self.issue).pack(side="left", padx=4)
        ttk.Button(btns, text="Return", command=self.return_book).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", command=self.delete).pack(side="left", padx=4)

        self.status = tk.Label(self, text="", anchor="w", bg="#e8eef5")
        self.status.pack(fill="x", side="bottom")

    def refresh(self, only_overdue=False):
        for r in self.tree.get_children():
            self.tree.delete(r)
        q = f"%{self.search_var.get().strip()}%"
        rows = self.con.execute(
            "SELECT id, title, author, issued_to, due_date FROM books "
            "WHERE title LIKE ? OR author LIKE ? ORDER BY id", (q, q)).fetchall()
        today = date.today().isoformat()
        total = issued = late = 0
        for id_, title, author, to, due in rows:
            is_late = bool(to) and due < today
            if only_overdue and not is_late:
                continue
            total += 1
            if to:
                issued += 1
            if is_late:
                late += 1
            status = f"Issued to {to}" if to else "Available"
            tag = "late" if is_late else ("out" if to else "free")
            self.tree.insert("", "end", iid=str(id_),
                             values=(id_, title, author, status, due or "-"), tags=(tag,))
        self.status.config(
            text=f"  Showing: {total}   |   Issued: {issued}   |   Overdue: {late}")

    def show_overdue(self):
        self.refresh(only_overdue=True)

    def show_all(self):
        self.search_var.set("")
        self.refresh()

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select a book", "Please select a book from the table first.")
            return None
        return int(sel[0])

    def add_book(self):
        title, author = self.title_var.get().strip(), self.author_var.get().strip()
        if not title or not author:
            messagebox.showwarning("Missing info", "Please enter both Title and Author.")
            return
        self.con.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
        self.con.commit()
        self.title_var.set("")
        self.author_var.set("")
        self.refresh()

    def issue(self):
        book_id = self.selected()
        if book_id is None:
            return
        if self.con.execute("SELECT issued_to FROM books WHERE id=?", (book_id,)).fetchone()[0]:
            messagebox.showwarning("Issued", "This book is already issued.")
            return
        name = simpledialog.askstring("Issue", "Student name:", parent=self)
        if not name or not name.strip():
            return
        due = (date.today() + timedelta(days=LOAN_DAYS)).isoformat()
        self.con.execute("UPDATE books SET issued_to=?, due_date=? WHERE id=?",
                         (name.strip(), due, book_id))
        self.con.commit()
        self.refresh()
        messagebox.showinfo("Done", f"Issued to {name.strip()}. Due date: {due}")

    def return_book(self):
        book_id = self.selected()
        if book_id is None:
            return
        to, due = self.con.execute(
            "SELECT issued_to, due_date FROM books WHERE id=?", (book_id,)).fetchone()
        if not to:
            messagebox.showinfo("Available", "This book is not issued.")
            return
        late = (date.today() - date.fromisoformat(due)).days
        msg = "Book returned successfully."
        if late > 0:
            msg += f"\nLate by {late} days. Fine: Rs {late * FINE_PER_DAY}"
        self.con.execute("UPDATE books SET issued_to=NULL, due_date=NULL WHERE id=?", (book_id,))
        self.con.commit()
        self.refresh()
        messagebox.showinfo("Return", msg)

    def delete(self):
        book_id = self.selected()
        if book_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this book permanently?"):
            self.con.execute("DELETE FROM books WHERE id=?", (book_id,))
            self.con.commit()
            self.refresh()


if __name__ == "__main__":
    App().mainloop()

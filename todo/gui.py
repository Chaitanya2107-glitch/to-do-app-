"""Tkinter desktop app."""
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from . import storage
from .export import to_csv


class App(ttk.Frame):
    def __init__(self, master, conn):
        super().__init__(master, padding=10)
        self.conn = conn
        self.selected_id = None
        self.pack(fill="both", expand=True)
        self._build()
        self.refresh()

    # ---------- layout ----------
    def _build(self):
        self.title_var = tk.StringVar()
        self.prio_var = tk.StringVar(value="medium")
        self.due_var = tk.StringVar()
        self.tag_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="all")
        self.sort_var = tk.StringVar(value="id")
        self.search_var = tk.StringVar()

        form = ttk.LabelFrame(self, text="Task", padding=8)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Title").grid(row=0, column=0, sticky="w")
        title = ttk.Entry(form, textvariable=self.title_var)
        title.grid(row=0, column=1, columnspan=5, sticky="ew", padx=4, pady=2)
        title.bind("<Return>", lambda e: self.add())
        title.focus()

        ttk.Label(form, text="Priority").grid(row=1, column=0, sticky="w")
        ttk.Combobox(form, textvariable=self.prio_var, values=storage.PRIORITIES,
                     state="readonly", width=8).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(form, text="Due (YYYY-MM-DD)").grid(row=1, column=2, sticky="e")
        ttk.Entry(form, textvariable=self.due_var, width=12).grid(row=1, column=3, padx=4)
        ttk.Label(form, text="Tag").grid(row=1, column=4, sticky="e")
        ttk.Entry(form, textvariable=self.tag_var, width=12).grid(row=1, column=5, padx=4)

        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=6, sticky="w", pady=(6, 0))
        ttk.Button(btns, text="Add", command=self.add).pack(side="left")
        ttk.Button(btns, text="Save changes", command=self.save).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", command=self.clear_form).pack(side="left")

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=8)
        ttk.Label(bar, text="Show").pack(side="left")
        f = ttk.Combobox(bar, textvariable=self.filter_var, values=["all", "pending", "done"],
                         state="readonly", width=8)
        f.pack(side="left", padx=4)
        ttk.Label(bar, text="Sort").pack(side="left")
        s = ttk.Combobox(bar, textvariable=self.sort_var, values=["id", "due", "priority"],
                         state="readonly", width=8)
        s.pack(side="left", padx=4)
        ttk.Label(bar, text="Search").pack(side="left")
        ttk.Entry(bar, textvariable=self.search_var, width=18).pack(side="left", padx=4)
        for w in (f, s):
            w.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.search_var.trace_add("write", lambda *a: self.refresh())

        cols = ("done", "title", "priority", "due", "tag")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for c, w in zip(cols, (50, 300, 80, 100, 90)):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=w, anchor="w" if c == "title" else "center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("done", foreground="#999999")
        self.tree.tag_configure("overdue", foreground="#cc2222")
        self.tree.tag_configure("high", foreground="#b8560b")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda e: self.toggle())
        self.tree.bind("<Delete>", lambda e: self.delete())

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Toggle done", command=self.toggle).pack(side="left")
        ttk.Button(actions, text="Delete", command=self.delete).pack(side="left", padx=4)
        ttk.Button(actions, text="Export CSV", command=self.export).pack(side="right")
        self.status = ttk.Label(actions, text="")
        self.status.pack(side="left", padx=12)

    # ---------- helpers ----------
    def _run(self, fn, *args, **kwargs):
        try:
            result = fn(self.conn, *args, **kwargs)
        except storage.TodoError as err:
            messagebox.showerror("Error", str(err))
            return False
        self.refresh()
        return result if result is not None else True

    def clear_form(self):
        self.selected_id = None
        self.title_var.set("")
        self.prio_var.set("medium")
        self.due_var.set("")
        self.tag_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def refresh(self):
        keep = self.selected_id
        self.tree.delete(*self.tree.get_children())
        rows = storage.list_tasks(self.conn, self.filter_var.get(),
                                  search=self.search_var.get() or None, sort=self.sort_var.get())
        today = date.today().isoformat()
        for r in rows:
            tags = []
            if r["done"]:
                tags.append("done")
            elif r["due"] and r["due"] < today:
                tags.append("overdue")
            elif r["priority"] == "high":
                tags.append("high")
            self.tree.insert("", "end", iid=str(r["id"]), tags=tags, values=(
                "✔" if r["done"] else "", r["title"], r["priority"], r["due"] or "", r["tag"] or ""))
        if keep is not None and self.tree.exists(str(keep)):
            self.tree.selection_set(str(keep))
        pending = sum(1 for r in rows if not r["done"])
        self.status.config(text=f"{len(rows)} shown, {pending} pending")

    # ---------- actions ----------
    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        task = storage.get_task(self.conn, int(sel[0]))
        self.selected_id = task["id"]
        self.title_var.set(task["title"])
        self.prio_var.set(task["priority"])
        self.due_var.set(task["due"] or "")
        self.tag_var.set(task["tag"] or "")

    def add(self):
        if self._run(storage.add_task, self.title_var.get(), self.prio_var.get(),
                     self.due_var.get().strip(), self.tag_var.get().strip()):
            self.clear_form()

    def save(self):
        if self.selected_id is None:
            messagebox.showinfo("Save changes", "Select a task first.")
            return
        self._run(storage.edit_task, self.selected_id, title=self.title_var.get(),
                  priority=self.prio_var.get(), due=self.due_var.get().strip(),
                  tag=self.tag_var.get().strip())

    def toggle(self):
        if self.selected_id is None:
            return
        task = storage.get_task(self.conn, self.selected_id)
        self._run(storage.set_done, self.selected_id, not task["done"])

    def delete(self):
        if self.selected_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this task?"):
            self._run(storage.delete_task, self.selected_id)
            self.clear_form()

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tasks.csv",
                                            filetypes=[("CSV", "*.csv")])
        if path:
            n = to_csv(storage.list_tasks(self.conn), path)
            messagebox.showinfo("Export", f"Exported {n} tasks.")


def run(conn=None):
    root = tk.Tk()
    root.title("Todo")
    root.geometry("680x520")
    root.minsize(560, 400)
    App(root, conn or storage.connect())
    root.mainloop()

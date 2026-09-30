"""Command-line interface."""
import argparse
import sys
from datetime import date

from . import __version__, storage
from .export import to_csv

COLORS = {"high": "\033[91m", "medium": "\033[93m", "low": "\033[92m"}
DIM, RESET = "\033[90m", "\033[0m"


def fmt(row):
    box = "[x]" if row["done"] else "[ ]"
    color = DIM if row["done"] else COLORS[row["priority"]]
    extras = []
    if row["due"]:
        overdue = not row["done"] and row["due"] < date.today().isoformat()
        extras.append(f"due {row['due']}" + (" (OVERDUE)" if overdue else ""))
    if row["tag"]:
        extras.append(f"#{row['tag']}")
    extra = f"  {DIM}{' '.join(extras)}{RESET}" if extras else ""
    return f"{color}{row['id']:>3} {box} {row['title']} ({row['priority']}){RESET}{extra}"


def build_parser():
    p = argparse.ArgumentParser(prog="todo", description="A simple todo manager.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a task")
    a.add_argument("title", nargs="+")
    a.add_argument("-p", "--priority", default="medium", choices=storage.PRIORITIES)
    a.add_argument("-d", "--due", help="YYYY-MM-DD")
    a.add_argument("-t", "--tag")

    l = sub.add_parser("list", help="list tasks")
    l.add_argument("--pending", action="store_true")
    l.add_argument("--done", action="store_true")
    l.add_argument("--tag")
    l.add_argument("--sort", default="id", choices=["id", "due", "priority"])

    for name, hlp in (("done", "mark done"), ("undone", "mark not done"), ("delete", "delete")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("id", type=int)

    e = sub.add_parser("edit", help="edit a task")
    e.add_argument("id", type=int)
    e.add_argument("--title")
    e.add_argument("-p", "--priority", choices=storage.PRIORITIES)
    e.add_argument("-d", "--due")
    e.add_argument("-t", "--tag")

    s = sub.add_parser("search", help="search titles")
    s.add_argument("text")

    x = sub.add_parser("export", help="export to CSV")
    x.add_argument("path", nargs="?", default="tasks.csv")

    sub.add_parser("gui", help="open the desktop app")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = storage.connect()
    try:
        if args.cmd == "add":
            tid = storage.add_task(conn, " ".join(args.title), args.priority, args.due, args.tag)
            print(f"Added task #{tid}")
        elif args.cmd == "list":
            status = "pending" if args.pending else "done" if args.done else "all"
            rows = storage.list_tasks(conn, status, args.tag, sort=args.sort)
            print("\n".join(map(fmt, rows)) or "No tasks found.")
        elif args.cmd in ("done", "undone"):
            storage.set_done(conn, args.id, args.cmd == "done")
            print(f"Task #{args.id} updated.")
        elif args.cmd == "delete":
            storage.delete_task(conn, args.id)
            print(f"Deleted task #{args.id}")
        elif args.cmd == "edit":
            storage.edit_task(conn, args.id, args.title, args.priority, args.due, args.tag)
            print(f"Task #{args.id} updated.")
        elif args.cmd == "search":
            rows = storage.list_tasks(conn, search=args.text)
            print("\n".join(map(fmt, rows)) or "No matches.")
        elif args.cmd == "export":
            n = to_csv(storage.list_tasks(conn), args.path)
            print(f"Exported {n} tasks to {args.path}")
        elif args.cmd == "gui":
            from .gui import run
            run(conn)
    except storage.TodoError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

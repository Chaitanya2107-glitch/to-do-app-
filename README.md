# Todo

A desktop todo app (Tkinter) with a CLI, SQLite storage, and CSV export.
No third-party dependencies needed to run it.

## Run the desktop app
```bash
python run_gui.py        # or: python -m todo gui
```
On some Linux distros you need Tkinter first: `sudo apt install python3-tk`.

Features: add/edit/delete tasks, priorities, due dates, tags, filter, sort,
live search, overdue highlighting, double-click to toggle done, CSV export.

## CLI
```bash
python -m todo add "Write report" -p high -d 2026-10-15 -t work
python -m todo list --pending --sort priority
python -m todo done 1
python -m todo edit 1 --title "Write final report"
python -m todo search report
python -m todo export tasks.csv
```
Tasks live in `~/.todo.db` (override with the `TODO_DB` env variable).

## Tests
```bash
pip install -r requirements.txt
python -m pytest
```

## Build a standalone app
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Todo run_gui.py
```
The executable appears in `dist/`.

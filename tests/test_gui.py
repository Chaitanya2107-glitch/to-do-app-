import pytest

tk = pytest.importorskip("tkinter")

from todo import storage
from todo.gui import App


@pytest.fixture
def app(tmp_path):
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available")
    root.withdraw()
    yield App(root, storage.connect(tmp_path / "gui.db"))
    root.destroy()


def test_add_shows_in_tree(app):
    app.title_var.set("Write tests")
    app.add()
    assert len(app.tree.get_children()) == 1
    assert app.title_var.get() == ""


def test_toggle_and_filter(app):
    app.title_var.set("a")
    app.add()
    iid = app.tree.get_children()[0]
    app.tree.selection_set(iid)
    app.update()  # let Tk deliver the selection event
    app.toggle()
    app.filter_var.set("pending")
    app.refresh()
    assert len(app.tree.get_children()) == 0

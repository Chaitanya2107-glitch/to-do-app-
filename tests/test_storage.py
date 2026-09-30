import pytest

from todo import storage
from todo.export import to_csv


@pytest.fixture
def conn(tmp_path):
    return storage.connect(tmp_path / "test.db")


def test_add_and_get(conn):
    tid = storage.add_task(conn, "Buy milk", "high", "2030-01-01", "home")
    task = storage.get_task(conn, tid)
    assert task["title"] == "Buy milk" and task["priority"] == "high"


def test_unique_ids(conn):
    a = storage.add_task(conn, "a")
    b = storage.add_task(conn, "b")
    assert a != b


def test_empty_title_rejected(conn):
    with pytest.raises(storage.TodoError):
        storage.add_task(conn, "   ")


def test_bad_priority_and_date(conn):
    with pytest.raises(storage.TodoError):
        storage.add_task(conn, "x", priority="urgent")
    with pytest.raises(storage.TodoError):
        storage.add_task(conn, "x", due="tomorrow")


def test_done_and_filter(conn):
    a = storage.add_task(conn, "a")
    storage.add_task(conn, "b")
    storage.set_done(conn, a)
    assert len(storage.list_tasks(conn, "pending")) == 1
    assert len(storage.list_tasks(conn, "done")) == 1


def test_delete(conn):
    tid = storage.add_task(conn, "a")
    storage.delete_task(conn, tid)
    with pytest.raises(storage.TodoError):
        storage.get_task(conn, tid)


def test_edit(conn):
    tid = storage.add_task(conn, "old")
    storage.edit_task(conn, tid, title="new", priority="low")
    task = storage.get_task(conn, tid)
    assert task["title"] == "new" and task["priority"] == "low"
    with pytest.raises(storage.TodoError):
        storage.edit_task(conn, tid)


def test_sort_priority_and_due(conn):
    storage.add_task(conn, "low", "low", "2030-01-03")
    storage.add_task(conn, "high", "high", "2030-01-02")
    storage.add_task(conn, "none", "medium")
    assert storage.list_tasks(conn, sort="priority")[0]["title"] == "high"
    assert storage.list_tasks(conn, sort="due")[-1]["title"] == "none"


def test_search_and_tag(conn):
    storage.add_task(conn, "write report", tag="work")
    storage.add_task(conn, "buy eggs", tag="home")
    assert len(storage.list_tasks(conn, search="report")) == 1
    assert len(storage.list_tasks(conn, tag="home")) == 1


def test_csv_export(conn, tmp_path):
    storage.add_task(conn, "a")
    out = tmp_path / "out.csv"
    assert to_csv(storage.list_tasks(conn), out) == 1
    assert out.read_text().startswith("id,title")

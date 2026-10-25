import json

import pytest

from research_history import (
    clear_research_history,
    delete_research_run,
    list_research_runs,
    save_research_run,
)


def test_save_and_list_research_runs(tmp_path):
    db = tmp_path / "history.sqlite3"
    run_id = save_research_run(
        "automated_discovery",
        "Pet gadgets",
        {"items": [{"name": "slow feeder", "score": 62}]},
        db_path=db,
    )

    runs = list_research_runs(db_path=db)

    assert runs[0]["id"] == run_id
    assert runs[0]["run_type"] == "automated_discovery"
    assert runs[0]["title"] == "Pet gadgets"
    assert runs[0]["payload"]["items"][0]["score"] == 62


def test_history_is_newest_first_and_limit_is_bounded(tmp_path):
    db = tmp_path / "history.sqlite3"
    save_research_run("agent", "First", {"n": 1}, db_path=db)
    save_research_run("agent", "Second", {"n": 2}, db_path=db)

    runs = list_research_runs(limit=1, db_path=db)

    assert len(runs) == 1
    assert runs[0]["title"] == "Second"


def test_delete_and_clear_history(tmp_path):
    db = tmp_path / "history.sqlite3"
    first = save_research_run("agent", "First", {}, db_path=db)
    save_research_run("agent", "Second", {}, db_path=db)

    assert delete_research_run(first, db_path=db) is True
    assert delete_research_run(first, db_path=db) is False
    assert clear_research_history(db_path=db) == 1
    assert list_research_runs(db_path=db) == []


def test_save_requires_type_and_title(tmp_path):
    with pytest.raises(ValueError):
        save_research_run(" ", "title", {}, db_path=tmp_path / "history.sqlite3")

"""Scaffolding smoke so `uv run pytest` collects before Django tests run."""


def test_pytest_collects() -> None:
    assert True

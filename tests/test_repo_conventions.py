from pathlib import Path


def test_pre_commit_lists_python_and_frontend_hooks() -> None:
    config = (
        Path(__file__)
        .resolve()
        .parent.parent.joinpath(".pre-commit-config.yaml")
        .read_text()
    )
    for hook_id in (
        "django-upgrade",
        "black",
        "isort",
        "flake8",
        "codespell",
        "prettier",
        "svelte-check",
    ):
        assert f"id: {hook_id}" in config

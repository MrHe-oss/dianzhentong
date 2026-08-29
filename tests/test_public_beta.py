from __future__ import annotations

from pathlib import Path

import pytest

from dianzhentong.config import (
    CLOUD_ENV,
    LOCAL_ENV,
    detect_environment,
    load_config,
    valid_issues_url,
)
from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.storage import ResilientPracticeRepository


def test_local_environment_and_storage_default():
    config = load_config({})
    assert config.environment == LOCAL_ENV
    assert config.storage_is_temporary is False
    assert config.storage_path.name == "practice.db"


def test_explicit_cloud_uses_temp_directory_not_repository():
    config = load_config({"DIANZHENTONG_ENV": "community_cloud"})
    project_root = Path(__file__).resolve().parent.parent
    assert config.environment == CLOUD_ENV
    assert config.storage_is_temporary is True
    assert project_root not in config.storage_path.parents


def test_explicit_database_path_wins_in_cloud(tmp_path):
    target = tmp_path / "cloud.db"
    config = load_config(
        {"DIANZHENTONG_ENV": "cloud", "DIANZHENTONG_DB_PATH": str(target)}
    )
    assert config.storage_path == target
    assert config.storage_is_temporary is False


@pytest.mark.parametrize(
    "environ",
    [
        {"STREAMLIT_SHARING_MODE": "true"},
        {"STREAMLIT_CLOUD": "1"},
        {"IS_STREAMLIT_CLOUD": "true"},
    ],
)
def test_cloud_signals_are_detected(environ):
    assert detect_environment(environ) == CLOUD_ENV


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "http://github.com/user/repo/issues",
        "https://example.com/user/repo/issues",
        "https://user@github.com/user/repo/issues",
        "https://github.com/user/repo",
    ],
)
def test_invalid_github_issues_urls_are_hidden(url):
    assert valid_issues_url(url) is None


def test_valid_github_issues_urls_are_kept():
    url = "https://github.com/example/dianzhentong/issues/new/choose"
    assert valid_issues_url(url) == url


def test_retired_feedback_environment_value_is_ignored():
    configured = load_config(
        {"DIANZHENTONG_ENV": "community_cloud", "DIANZHENTONG_FEEDBACK_URL": "invalid"}
    )
    assert configured.environment == CLOUD_ENV
    assert not hasattr(configured, "feedback_url")


def test_unwritable_database_falls_back_and_practice_still_saves(tmp_path):
    directory_instead_of_file = tmp_path / "not-a-database"
    directory_instead_of_file.mkdir()
    repository = ResilientPracticeRepository(directory_instead_of_file)
    assert repository.persistent is False

    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_control_power")
    session.answer("异常")
    assert repository.save(session.to_practice_record("2026-08-29T12:00:00+08:00")) is True
    assert repository.summary()["attempts"] == 1


def test_gitignore_protects_local_state_and_secrets():
    content = Path(".gitignore").read_text(encoding="utf-8")
    for expected in ["data/*.db", ".streamlit/secrets.toml", ".venv/", "*.log"]:
        assert expected in content


def test_public_app_keeps_pyarrow_backed_components_disabled():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "st.dataframe(" not in source
    assert "st.table(" not in source


def test_deployment_files_exist():
    required = [
        "runtime.txt", ".streamlit/config.toml", "LICENSE", "CONTRIBUTING.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/experience.yml",
        ".github/ISSUE_TEMPLATE/content_correction.yml",
    ]
    assert all(Path(path).exists() for path in required)


def test_questionnaire_is_removed_but_issue_entry_remains():
    source = Path("app.py").read_text(encoding="utf-8")
    config_source = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert "feedback_url" not in source
    assert "DIANZHENTONG_FEEDBACK_URL" not in config_source
    assert "程序故障或专业纠错" in source


def test_four_step_ui_and_mobile_theme_are_present():
    source = Path("app.py").read_text(encoding="utf-8")
    assert 'steps = ["选择实验", "安全确认", "逐步排查", "学习报告"]' in source
    assert "stage / 4" in source
    assert "UI_STATE_VERSION" in source
    assert "@media(max-width:640px)" in source


def test_guided_learning_and_knowledge_center_are_present():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "引导学习模式" in source
    assert "知识中心" in source
    assert 'set_stage(6)' in source
    assert 'current_mode in {"随机故障练习", "引导学习模式"}' in source
    assert "if scored_practice:" in source
    assert "repository.save(session.to_practice_record())" in source

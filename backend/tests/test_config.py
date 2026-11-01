"""Settings must load from the shipped .env.example exactly as Docker Compose passes it."""
from pathlib import Path

import pytest

from app.core.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"


def _env_lines() -> dict[str, str]:
    out = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            out[key] = value
    return out


def test_env_example_has_no_inline_comments():
    for key, value in _env_lines().items():
        assert "#" not in value, f"{key} has an inline comment; move it to its own line"


def test_settings_load_from_env_example_as_environment(monkeypatch):
    for key, value in _env_lines().items():
        monkeypatch.setenv(key, value)
    s = Settings(_env_file=None)
    assert s.cors_origin_list == ["http://localhost:3000"]
    assert s.environment == "development"
    assert s.access_token_minutes == 10080


def test_settings_load_from_env_file(tmp_path, monkeypatch):
    for key in _env_lines():
        monkeypatch.delenv(key, raising=False)
    env = tmp_path / ".env"
    env.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    s = Settings(_env_file=str(env))
    assert s.cors_origin_list == ["http://localhost:3000"]


@pytest.mark.parametrize("raw, expected", [
    ("http://a.com", ["http://a.com"]),
    ("http://a.com, http://b.com ,", ["http://a.com", "http://b.com"]),
    ('["http://a.com","http://b.com"]', ["http://a.com", "http://b.com"]),
])
def test_cors_origin_formats(monkeypatch, raw, expected):
    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert Settings(_env_file=None).cors_origin_list == expected

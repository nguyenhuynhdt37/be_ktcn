import json
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "data"
    / "postgraduate_programs.json"
)


def load_program() -> dict:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert len(payload["programs"]) == 1
    return payload["programs"][0]


def test_postgraduate_seed_contains_localized_programme_profile():
    program = load_program()

    assert program["department_code"] == "FIT"
    assert program["code"] == "60.48.02.01"
    assert program["degree_level"] == "master"
    assert program["duration_years"] == 2
    assert {"vi", "en"} <= program["translations"].keys()
    assert program["translations"]["vi"]["admissions_info"]

    version = program["profile"]["versions"][0]
    assert version["version_year"] == 2017
    assert version["total_credits"] == 39
    assert version["is_current"] is False
    assert version["documents"][0]["document_type"] == "source_page"


def test_postgraduate_curriculum_matches_published_structure():
    version = load_program()["profile"]["versions"][0]
    courses = [row for row in version["courses"] if row["row_type"] == "course"]
    groups = [row for row in version["courses"] if row["row_type"] == "group"]
    summary = [row for row in version["courses"] if row["row_type"] == "summary"]

    assert len(courses) == 20
    assert len(groups) == 4
    assert len(summary) == 1
    assert len({course["course_code"] for course in courses}) == 20
    assert sum(course["credits"] for course in courses[:7]) == 21
    assert summary[0]["credits"] == 39
    assert all({"vi", "en"} <= row["translations"].keys() for row in version["courses"])

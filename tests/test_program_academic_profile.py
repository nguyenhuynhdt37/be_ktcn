import pytest
from pydantic import ValidationError

from app.modules.program.schemas import ProgramAcademicProfileInput
from scripts.import_electronics_program import build_profile


def test_electronics_program_profile_matches_crawled_dataset() -> None:
    profile = build_profile()
    current_version = next(
        version for version in profile.versions if version.is_current
    )

    assert len(profile.versions) == 3
    assert current_version.version_year == 2022
    assert current_version.cohort_code == "K62"
    assert sum(len(version.documents) for version in profile.versions) == 6
    assert len(current_version.documents) == 2
    assert len(current_version.outcomes) == 13
    assert len(current_version.courses) == 58
    assert {course.row_type for course in current_version.courses} == {
        "course",
        "group",
        "placeholder",
        "summary",
    }


def test_academic_profile_rejects_multiple_current_versions() -> None:
    payload = build_profile().model_dump()
    payload["versions"][1]["is_current"] = True

    with pytest.raises(ValidationError):
        ProgramAcademicProfileInput.model_validate(payload)

import pytest

from scripts.import_remaining_programs import PROGRAMS

EXPECTED_PROFILE_COUNTS = {
    "7520216": (3, 3, 114, 66),
    "52510301": (1, 0, 22, 58),
    "7480201": (1, 1, 21, 89),
    "7480201-CLC": (1, 0, 0, 52),
    "7510205": (1, 0, 0, 77),
    "7510206": (1, 0, 40, 0),
    "7520210": (1, 0, 13, 61),
}


@pytest.mark.parametrize("definition", PROGRAMS, ids=lambda item: item.code)
def test_remaining_program_profile_matches_crawled_dataset(definition) -> None:
    profile = definition.build_profile()
    current = next(version for version in profile.versions if version.is_current)
    actual = (
        len(profile.versions),
        sum(len(version.documents) for version in profile.versions),
        len(current.outcomes),
        len(current.courses),
    )

    assert actual == EXPECTED_PROFILE_COUNTS[definition.code]
    assert len({item.code for item in current.outcomes}) == len(current.outcomes)
    course_codes = [item.course_code for item in current.courses if item.course_code]
    assert len(set(course_codes)) == len(course_codes)


def test_pdf_profiles_include_curriculum_metadata_and_it_careers() -> None:
    profiles = {definition.code: definition.build_profile() for definition in PROGRAMS}
    automation = profiles["7520216"].versions[0]
    information_technology = profiles["7480201"].versions[0]

    assert automation.total_credits == 150
    assert information_technology.total_credits == 150
    assert any(item.course_code == "AUT30016" for item in automation.courses)
    assert any(
        item.course_code == "INF30057" for item in information_technology.courses
    )
    assert "Chuyên viên kiểm thử phần mềm" in (
        information_technology.translations["vi"].career_opportunities or ""
    )

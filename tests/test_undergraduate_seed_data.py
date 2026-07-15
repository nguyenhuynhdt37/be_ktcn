import json
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "data"
    / "undergraduate_programs.json"
)
EXPECTED_CODES = {
    "7520207",
    "7520216",
    "52510301",
    "7480201",
    "7480201-CLC",
    "7510205",
    "7510206",
    "7520210",
}


def test_undergraduate_seed_is_complete_and_consistent():
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert {program["code"] for program in payload["programs"]} == EXPECTED_CODES

    for program in payload["programs"]:
        assert {"vi", "en"} <= program["translations"].keys()
        assert program["profile"]["versions"]

        years = [version["version_year"] for version in program["profile"]["versions"]]
        assert len(years) == len(set(years))

        for version in program["profile"]["versions"]:
            outcome_keys = [
                (outcome["code"], outcome["outcome_type"])
                for outcome in version["outcomes"]
            ]
            assert len(outcome_keys) == len(set(outcome_keys))

            course_codes = [
                course["course_code"]
                for course in version["courses"]
                if course["course_code"] is not None
            ]
            assert len(course_codes) == len(set(course_codes))


def test_pdf_enrichment_is_included_in_seed_snapshot():
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    programmes = {program["code"]: program for program in payload["programs"]}

    automation = next(
        version
        for version in programmes["7520216"]["profile"]["versions"]
        if version["is_current"]
    )
    information_technology = next(
        version
        for version in programmes["7480201"]["profile"]["versions"]
        if version["is_current"]
    )

    assert (automation["total_credits"], len(automation["courses"])) == (150, 66)
    assert (
        information_technology["total_credits"],
        len(information_technology["courses"]),
    ) == (150, 89)
    assert information_technology["translations"]["vi"]["career_opportunities"]

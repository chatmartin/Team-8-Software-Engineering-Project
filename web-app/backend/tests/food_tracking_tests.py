from flask_service.recommendations import _score_meal
from flask_service.spoonacular_api_calls import normalize_unit, normalize_unit_name


def test_unit_normalization_handles_common_mass_units():
    assert normalize_unit(1000, "mg", "g") == 1
    assert normalize_unit(2, "g", "mg") == 2000
    assert normalize_unit_name("mcg") == "ug"


def test_recommendation_score_excludes_high_severity_sensitivity():
    meal = {
        "meal": "Peanut noodles",
        "ingredients": [{"name": "peanut sauce"}],
        "nutrients": {"protein": {"amount": 20}},
        "flags": [],
    }
    score = _score_meal(
        meal,
        goals=[{"nutrient": "protein", "target": 100, "min_max": "min"}],
        progress={"protein": {"total": 10}},
        sensitivities=[{"ingredient": "peanut", "severity": "high"}],
    )
    assert score is None


def test_recommendation_score_rewards_under_target_nutrients():
    meal = {
        "meal": "Lentil bowl",
        "ingredients": [{"name": "lentils"}],
        "nutrients": {"protein": {"amount": 25}},
        "flags": [],
    }
    score = _score_meal(
        meal,
        goals=[{"nutrient": "protein", "target": 100, "min_max": "min"}],
        progress={"protein": {"total": 25}},
        sensitivities=[],
    )
    assert score["score"] > 50
    assert "helps with protein" in score["signals"]

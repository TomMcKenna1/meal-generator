import pytest
from src.meal_generator.models import DataSource
from src.meal_generator.nutrient_profile import NutrientProfile


def test_nutrient_profile_creation():
    """Tests successful creation with default and specified values."""
    profile = NutrientProfile()
    assert profile.energy == 0.0
    assert not profile.contains_dairy
    assert profile.data_source == DataSource.ESTIMATED_MODEL


@pytest.mark.parametrize(
    "field, value",
    [
        ("energy", -100),
        ("fats", -5.0),
        ("protein", -1),
    ],
)
def test_nutrient_profile_negative_values(field, value):
    """Tests that negative numerical values raise a ValueError."""
    with pytest.raises(ValueError, match=f"'{field}' cannot be negative"):
        NutrientProfile(**{field: value})


@pytest.mark.parametrize(
    "field, value",
    [
        ("energy", "invalid"),
        ("carbohydrates", None),
        ("salt", []),
    ],
)
def test_nutrient_profile_invalid_types(field, value):
    """Tests that non-numeric values for numerical fields raise a TypeError."""
    with pytest.raises(TypeError, match=f"'{field}' must be a numeric value"):
        NutrientProfile(**{field: value})


def test_nutrient_profile_as_dict():
    """Tests the serialization of the NutrientProfile to a dictionary."""
    profile = NutrientProfile(
        energy=100, protein=10, data_source=DataSource.RETRIEVED_API
    )
    profile_dict = profile.as_dict()
    assert isinstance(profile_dict, dict)
    assert profile_dict["energy"] == 100.0
    assert profile_dict["protein"] == 10.0
    assert profile_dict["data_source"] == "retrieved_api"


def test_nutrient_profile_addition_with_data_source():
    """Tests the data_source aggregation logic."""
    p1 = NutrientProfile(energy=100, data_source=DataSource.RETRIEVED_API)
    p2 = NutrientProfile(energy=50, data_source=DataSource.ESTIMATED_MODEL)
    p3 = NutrientProfile(energy=20, data_source=DataSource.ESTIMATED_WITH_CONTEXT)

    result1 = p1 + p2
    assert result1.energy == 150.0
    assert result1.data_source == DataSource.ESTIMATED_MODEL

    result2 = p1 + p3
    assert result2.energy == 120.0
    assert result2.data_source == DataSource.ESTIMATED_WITH_CONTEXT

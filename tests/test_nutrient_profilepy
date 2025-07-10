import pytest
from src.meal_generator.nutrient_profile import NutrientProfile

def test_nutrient_profile_creation():
    """Tests successful creation with default and specified values."""
    profile = NutrientProfile()
    assert profile.energy == 0.0
    assert not profile.contains_dairy

    profile_custom = NutrientProfile(energy=200, protein=25.5, contains_gluten=True)
    assert profile_custom.energy == 200.0
    assert profile_custom.protein == 25.5
    assert profile_custom.contains_gluten

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
    profile = NutrientProfile(energy=100, protein=10, is_ultra_processed=True)
    profile_dict = profile.as_dict()
    assert isinstance(profile_dict, dict)
    assert profile_dict["energy"] == 100.0
    assert profile_dict["protein"] == 10.0
    assert profile_dict["is_ultra_processed"] is True
    assert "sugars" in profile_dict
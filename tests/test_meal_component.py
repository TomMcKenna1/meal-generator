from src.meal_generator.meal_component import MealComponent
from src.meal_generator.nutrient_profile import NutrientProfile


def test_meal_component_creation(meal_component_fixt: MealComponent):
    """Tests successful creation of a MealComponent."""
    assert meal_component_fixt.name == "Grilled Chicken Breast"
    assert meal_component_fixt.brand == "Farm Fresh"
    assert meal_component_fixt.total_weight == 120.0
    assert isinstance(meal_component_fixt.nutrient_profile, NutrientProfile)


def test_meal_component_as_dict(meal_component_fixt: MealComponent):
    """Tests the serialization of a MealComponent to a dictionary."""
    component_dict = meal_component_fixt.as_dict()
    assert component_dict["name"] == "Grilled Chicken Breast"
    assert component_dict["brand"] == "Farm Fresh"
    assert "nutrientProfile" in component_dict
    assert component_dict["nutrientProfile"]["energy"] == 150.0

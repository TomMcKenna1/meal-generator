import pytest
from src.meal_generator.meal import Meal
from src.meal_generator.meal_component import MealComponent
from src.meal_generator.nutrient_profile import NutrientProfile


@pytest.fixture
def sample_meal(meal_component_fixt: MealComponent) -> Meal:
    """Provides a sample Meal instance with one component."""
    return Meal(
        name="Chicken Salad",
        description="A simple chicken salad.",
        component_list=[meal_component_fixt],
    )


def test_meal_creation(sample_meal: Meal):
    """Tests the successful creation of a Meal."""
    assert sample_meal.name == "Chicken Salad"
    assert len(sample_meal.component_list) == 1


@pytest.mark.parametrize(
    "name, description, components, error",
    [
        ("", "A meal", [True], "Meal name cannot be empty."),
        ("A meal", "", [True], "Meal description cannot be empty."),
        ("A meal", "A description", [], "Meal must contain at least one component."),
    ],
)
def test_meal_creation_invalid(name, description, components, error):
    """Tests that invalid initialization parameters raise a ValueError."""
    with pytest.raises(ValueError, match=error):
        Meal(name=name, description=description, component_list=components)


def test_aggregate_nutrients():
    """Tests the nutrient aggregation logic."""
    component1 = MealComponent(
        "C1", "1", 100, NutrientProfile(energy=100, protein=10, contains_dairy=True)
    )
    component2 = MealComponent(
        "C2", "1", 50, NutrientProfile(energy=50, protein=5, contains_gluten=True)
    )
    meal = Meal("Test Meal", "Desc", [component1, component2])

    assert meal.nutrient_profile.energy == 150.0
    assert meal.nutrient_profile.protein == 15.0
    assert meal.nutrient_profile.contains_dairy is True
    assert meal.nutrient_profile.contains_gluten is True
    assert meal.nutrient_profile.contains_histamines is False


def test_add_component(sample_meal: Meal):
    """Tests adding a component to a meal."""
    initial_energy = sample_meal.nutrient_profile.energy
    new_component = MealComponent("Lettuce", "50g", 50, NutrientProfile(energy=10))

    sample_meal.add_component(new_component)

    assert len(sample_meal.component_list) == 2
    assert sample_meal.nutrient_profile.energy == initial_energy + 10.0


def test_as_dict(sample_meal: Meal):
    """Tests the serialization of a Meal object to a dictionary."""
    meal_dict = sample_meal.as_dict()
    assert meal_dict["name"] == "Chicken Salad"
    assert "id" in meal_dict
    assert isinstance(meal_dict["components"], list)
    assert len(meal_dict["components"]) == 1
    assert "nutrient_profile" in meal_dict

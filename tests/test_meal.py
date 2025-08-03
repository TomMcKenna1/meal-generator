import pytest
from unittest.mock import AsyncMock, MagicMock
from src.meal_generator.models import MealType, ComponentType
from src.meal_generator.meal import Meal
from src.meal_generator.meal_component import MealComponent
from src.meal_generator.nutrient_profile import NutrientProfile


@pytest.fixture
def sample_meal(meal_component_fixt: MealComponent) -> Meal:
    """Provides a sample Meal instance with one component."""
    return Meal(
        name="Chicken Salad",
        description="A simple chicken salad.",
        meal_type=MealType.MEAL,
        component_list=[meal_component_fixt],
    )


def test_meal_creation(sample_meal: Meal):
    """Tests the successful creation of a Meal."""
    assert sample_meal.name == "Chicken Salad"
    assert len(sample_meal.component_list) == 1


def test_add_component(sample_meal: Meal):
    """Tests adding a component to a meal."""
    initial_energy = sample_meal.nutrient_profile.energy
    new_component = MealComponent(
        "Lettuce", "50g", 50, ComponentType.FOOD, NutrientProfile(energy=10)
    )
    sample_meal.add_component(new_component)
    assert len(sample_meal.component_list) == 2
    assert sample_meal.nutrient_profile.energy == initial_energy + 10.0


def test_add_component_from_string(sample_meal: Meal):
    """Tests adding a component from a natural language string."""
    mock_generator = MagicMock()
    new_component = MealComponent(
        name="A dollop of mayo",
        quantity="1 tbsp",
        total_weight=15,
        component_type=ComponentType.FOOD,
        nutrient_profile=NutrientProfile(energy=100, fats=11),
    )
    mock_generator.generate_component.return_value = [new_component]

    sample_meal.add_component_from_string("a dollop of mayo", mock_generator, "GB")

    mock_generator.generate_component.assert_called_once_with("a dollop of mayo", "GB")
    assert len(sample_meal.component_list) == 2
    assert sample_meal.nutrient_profile.energy == 250.0
    assert any(c.name == "A dollop of mayo" for c in sample_meal.component_list)


@pytest.mark.asyncio
async def test_add_component_from_string_async(sample_meal: Meal):
    """Tests adding a component asynchronously from a natural language string."""
    mock_generator = MagicMock()
    new_component = MealComponent(
        name="A dollop of mayo",
        quantity="1 tbsp",
        total_weight=15,
        component_type=ComponentType.FOOD,
        nutrient_profile=NutrientProfile(energy=100, fats=11),
    )
    mock_generator.generate_component_async = AsyncMock(return_value=[new_component])

    await sample_meal.add_component_from_string_async(
        "a dollop of mayo", mock_generator, "GB"
    )

    mock_generator.generate_component_async.assert_awaited_once_with(
        "a dollop of mayo", "GB"
    )
    assert len(sample_meal.component_list) == 2
    assert sample_meal.nutrient_profile.energy == 250.0
    assert any(c.name == "A dollop of mayo" for c in sample_meal.component_list)


def test_remove_component(sample_meal: Meal, meal_component_fixt: MealComponent):
    """Tests removing a component and verifies nutrient recalculation."""
    sample_meal.remove_component(meal_component_fixt.id)
    assert len(sample_meal.component_list) == 0
    assert sample_meal.nutrient_profile.energy == 0
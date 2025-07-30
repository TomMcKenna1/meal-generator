import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from src.meal_generator.models import MealType, ComponentType
from src.meal_generator.meal import (
    Meal,
    DuplicateComponentIDError,
    ComponentDoesNotExist,
)
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
        Meal(
            name=name,
            description=description,
            meal_type=MealType.MEAL,
            component_list=components,
        )


def test_aggregate_nutrients():
    """Tests the nutrient aggregation logic."""
    component1 = MealComponent(
        "C1",
        "1",
        100,
        ComponentType.FOOD,
        NutrientProfile(energy=100, protein=10, contains_dairy=True),
    )
    component2 = MealComponent(
        "C2",
        "1",
        50,
        ComponentType.FOOD,
        NutrientProfile(energy=50, protein=5, contains_gluten=True),
    )
    meal = Meal("Test Meal", "Desc", MealType.MEAL, [component1, component2])

    assert meal.nutrient_profile.energy == 150.0
    assert meal.nutrient_profile.protein == 15.0
    assert meal.nutrient_profile.contains_dairy is True
    assert meal.nutrient_profile.contains_gluten is True
    assert meal.nutrient_profile.contains_histamines is False


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
    mock_generator.generate_component.return_value = new_component

    initial_component_count = len(sample_meal.component_list)
    initial_energy = sample_meal.nutrient_profile.energy

    sample_meal.add_component_from_string("a dollop of mayo", mock_generator)

    mock_generator.generate_component.assert_called_once_with(
        "a dollop of mayo", sample_meal
    )
    assert len(sample_meal.component_list) == initial_component_count + 1
    assert sample_meal.nutrient_profile.energy == initial_energy + 100
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
    mock_generator.generate_component_async = AsyncMock(return_value=new_component)

    initial_component_count = len(sample_meal.component_list)
    initial_energy = sample_meal.nutrient_profile.energy
    natural_language_string = "a dollop of mayo"

    await sample_meal.add_component_from_string_async(
        natural_language_string, mock_generator
    )

    mock_generator.generate_component_async.assert_awaited_once_with(
        natural_language_string, sample_meal
    )
    assert len(sample_meal.component_list) == initial_component_count + 1
    assert sample_meal.nutrient_profile.energy == initial_energy + 100
    assert any(c.name == "A dollop of mayo" for c in sample_meal.component_list)


def test_add_duplicate_component_raises_error(
    sample_meal: Meal, meal_component_fixt: MealComponent
):
    """Tests that adding a component with a duplicate ID raises an error."""
    with pytest.raises(
        DuplicateComponentIDError,
        match=f"Component with id: {meal_component_fixt.id} already exists",
    ):
        sample_meal.add_component(meal_component_fixt)


def test_remove_component(sample_meal: Meal, meal_component_fixt: MealComponent):
    """Tests removing a component and verifies nutrient recalculation."""
    new_component = MealComponent(
        "Tomato", "30g", 30, ComponentType.FOOD, NutrientProfile(energy=15, protein=1)
    )
    sample_meal.add_component(new_component)

    assert len(sample_meal.component_list) == 2
    assert sample_meal.nutrient_profile.energy == 165.0
    assert sample_meal.nutrient_profile.protein == 16.0

    sample_meal.remove_component(meal_component_fixt.id)

    assert len(sample_meal.component_list) == 1
    assert sample_meal.get_component_by_id(meal_component_fixt.id) is None
    assert sample_meal.nutrient_profile.energy == 15.0
    assert sample_meal.nutrient_profile.protein == 1.0


def test_remove_nonexistent_component_raises_error(sample_meal: Meal):
    """Tests that trying to remove a component that does not exist raises an error."""
    non_existent_id = uuid.uuid4()
    with pytest.raises(
        ComponentDoesNotExist, match=f"Component id: {non_existent_id} does not exist"
    ):
        sample_meal.remove_component(non_existent_id)


def test_as_dict(sample_meal: Meal):
    """Tests the serialization of a Meal object to a dictionary."""
    meal_dict = sample_meal.as_dict()
    assert meal_dict["name"] == "Chicken Salad"
    assert "id" in meal_dict
    assert isinstance(meal_dict["components"], list)
    assert len(meal_dict["components"]) == 1
    assert "nutrient_profile" in meal_dict

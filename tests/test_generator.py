import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.meal_generator.models import ComponentType, MealType
from src.meal_generator.generator import MealGenerator, MealGenerationError
from src.meal_generator.meal import Meal
from src.meal_generator.meal_component import MealComponent
from src.meal_generator.nutrient_profile import NutrientProfile

ERROR_SCENARIOS = [
    (
        '{"status": "bad_input"}',
        "Input was determined to be malicious.",
    ),
    (
        '{"status": "ok", "result": null}',
        "AI response status was 'ok' but no object data was provided.",
    ),
    (
        '{"status": "ok", "result": {"name": "x", "description": "y", "type": "meal", "components": [{"name": "c", "type": "meal", "quantity": "1", "totalWeight": 1.0, "nutrientProfile": {"energy": "invalid"}}]}}',
        "AI response failed validation",
    ),
    (
        '{"data": "wrong_structure"}',
        "AI response failed validation",
    ),
    (
        "this is not a valid json string",
        "AI response failed validation",
    ),
]


@pytest.fixture
def valid_api_response() -> dict:
    """
    Provides a valid, structured API response that conforms to the Pydantic schema.
    """
    return {
        "status": "ok",
        "result": {
            "name": "Scrambled Eggs on Toast",
            "description": "A classic breakfast dish.",
            "type": "meal",
            "components": [
                {
                    "name": "Scrambled Eggs",
                    "brand": None,
                    "quantity": "2 large",
                    "type": "food",
                    "totalWeight": 120.0,
                    "nutrientProfile": {
                        "energy": 180.0,
                        "fats": 14.0,
                        "saturatedFats": 5.0,
                        "carbohydrates": 1.0,
                        "sugars": 1.0,
                        "fibre": 0.0,
                        "protein": 15.0,
                        "salt": 0.2,
                        "containsDairy": True,
                    },
                },
                {
                    "name": "Whole Wheat Toast",
                    "brand": "Hovis",
                    "quantity": "2 slices",
                    "type": "food",
                    "totalWeight": 60.0,
                    "nutrientProfile": {
                        "energy": 160.0,
                        "fats": 2.0,
                        "saturatedFats": 0.5,
                        "carbohydrates": 30.0,
                        "sugars": 3.0,
                        "fibre": 4.0,
                        "protein": 8.0,
                        "salt": 0.4,
                        "containsGluten": True,
                        "isProcessed": True,
                    },
                },
            ],
        },
    }


@pytest.fixture
def valid_component_api_response() -> dict:
    """
    Provides a valid, structured API response for a single component.
    """
    return {
        "status": "ok",
        "result": {
            "name": "Olive Oil",
            "brand": "Extra Virgin",
            "quantity": "1 tbsp",
            "type": "food",
            "totalWeight": 14.0,
            "nutrientProfile": {
                "energy": 120.0,
                "fats": 14.0,
                "saturatedFats": 2.0,
                "carbohydrates": 0.0,
                "sugars": 0.0,
                "fibre": 0.0,
                "protein": 0.0,
                "salt": 0.0,
            },
        },
    }


@pytest.fixture
def sample_meal_for_context() -> Meal:
    """Provides a sample Meal instance to be used as context."""
    component = MealComponent(
        name="Grilled Chicken Breast",
        quantity="1 breast",
        total_weight=120,
        component_type=ComponentType.FOOD,
        nutrient_profile=NutrientProfile(energy=150, protein=30),
    )
    return Meal(
        name="Chicken Dish",
        description="A simple dish with chicken.",
        meal_type=MealType.MEAL,
        component_list=[component],
    )


@patch("src.meal_generator.generator.genai")
def test_generate_meal_success(mock_genai: MagicMock, valid_api_response: dict):
    """Tests a successful end-to-end meal generation."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(valid_api_response)
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    generator = MealGenerator(api_key="dummy_key")
    meal = generator.generate_meal("two scrambled eggs on hovis toast")

    mock_genai.Client.return_value.models.generate_content.assert_called_once()
    assert isinstance(meal, Meal)
    assert meal.name == "Scrambled Eggs on Toast"
    assert len(meal.component_list) == 2
    assert meal.component_list[0].type == ComponentType.FOOD
    assert meal.nutrient_profile.energy == 340.0
    assert meal.nutrient_profile.protein == 23.0
    assert meal.nutrient_profile.contains_gluten is True


def test_generate_meal_empty_input():
    """Tests that an empty input string raises a ValueError."""
    generator = MealGenerator(api_key="dummy_key")
    with pytest.raises(
        ValueError, match="Natural language string cannot be empty for meal generation."
    ):
        generator.generate_meal("")


@pytest.mark.parametrize(
    "api_response_text, expected_error_message",
    ERROR_SCENARIOS,
)
@patch("src.meal_generator.generator.genai")
def test_generate_meal_error_scenarios(
    mock_genai: MagicMock, api_response_text, expected_error_message
):
    """Tests that various invalid API responses raise MealGenerationError."""
    mock_response = MagicMock()
    mock_response.text = api_response_text
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response

    generator = MealGenerator(api_key="dummy_key")

    with pytest.raises(MealGenerationError, match=expected_error_message):
        generator.generate_meal("some meal")


@pytest.mark.asyncio
@patch("src.meal_generator.generator.genai")
async def test_generate_meal_async_success(
    mock_genai: MagicMock, valid_api_response: dict
):
    """Tests a successful end-to-end asynchronous meal generation."""
    mock_async_response = MagicMock()
    mock_async_response.text = json.dumps(valid_api_response)

    mock_genai.Client.return_value.aio.models.generate_content = AsyncMock(
        return_value=mock_async_response
    )

    generator = MealGenerator(api_key="dummy_key")
    meal = await generator.generate_meal_async("two scrambled eggs on hovis toast")

    mock_genai.Client.return_value.aio.models.generate_content.assert_awaited_once()
    assert isinstance(meal, Meal)
    assert meal.name == "Scrambled Eggs on Toast"
    assert len(meal.component_list) == 2
    assert meal.component_list[0].type == ComponentType.FOOD
    assert meal.nutrient_profile.energy == 340.0
    assert meal.nutrient_profile.protein == 23.0
    assert meal.nutrient_profile.contains_gluten is True


@pytest.mark.asyncio
async def test_generate_meal_async_empty_input():
    """Tests that an empty input string raises a ValueError in the async method."""
    generator = MealGenerator(api_key="dummy_key")
    with pytest.raises(ValueError, match="Natural language string cannot be empty."):
        await generator.generate_meal_async("")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "api_response_text, expected_error_message",
    ERROR_SCENARIOS,
)
@patch("src.meal_generator.generator.genai")
async def test_generate_meal_async_error_scenarios(
    mock_genai: MagicMock, api_response_text: str, expected_error_message: str
):
    """
    Tests that various invalid API responses raise MealGenerationError in the async method.
    """
    mock_async_response = MagicMock()
    mock_async_response.text = api_response_text
    mock_genai.Client.return_value.aio.models.generate_content = AsyncMock(
        return_value=mock_async_response
    )

    generator = MealGenerator(api_key="dummy_key")

    with pytest.raises(MealGenerationError, match=expected_error_message):
        await generator.generate_meal_async("some meal")


@patch("src.meal_generator.generator.genai")
def test_generate_component_success(
    mock_genai: MagicMock,
    valid_component_api_response: dict,
    sample_meal_for_context: Meal,
):
    """Tests successful single component generation."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(valid_component_api_response)
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response

    generator = MealGenerator(api_key="dummy_key")
    component = generator.generate_component(
        "a tbsp of olive oil", sample_meal_for_context
    )

    mock_genai.Client.return_value.models.generate_content.assert_called_once()
    assert isinstance(component, MealComponent)
    assert component.name == "Olive Oil"
    assert component.type == ComponentType.FOOD
    assert component.nutrient_profile.energy == 120.0
    assert component.total_weight == 14.0


@pytest.mark.asyncio
@patch("src.meal_generator.generator.genai")
async def test_generate_component_async_success(
    mock_genai: MagicMock,
    valid_component_api_response: dict,
    sample_meal_for_context: Meal,
):
    """Tests successful async single component generation."""
    mock_async_response = MagicMock()
    mock_async_response.text = json.dumps(valid_component_api_response)
    mock_genai.Client.return_value.aio.models.generate_content = AsyncMock(
        return_value=mock_async_response
    )

    generator = MealGenerator(api_key="dummy_key")
    component = await generator.generate_component_async(
        "a tbsp of olive oil", sample_meal_for_context
    )

    mock_genai.Client.return_value.aio.models.generate_content.assert_awaited_once()
    assert isinstance(component, MealComponent)
    assert component.name == "Olive Oil"
    assert component.type == ComponentType.FOOD
    assert component.nutrient_profile.energy == 120.0
    assert component.total_weight == 14.0


def test_generate_component_empty_input(sample_meal_for_context: Meal):
    """Tests that an empty input string raises a ValueError for component generation."""
    generator = MealGenerator(api_key="dummy_key")
    with pytest.raises(ValueError, match="Natural language string cannot be empty."):
        generator.generate_component("", sample_meal_for_context)


@pytest.mark.asyncio
async def test_generate_component_async_empty_input(sample_meal_for_context: Meal):
    """Tests that an empty input string raises a ValueError in the async component method."""
    generator = MealGenerator(api_key="dummy_key")
    with pytest.raises(ValueError, match="Natural language string cannot be empty."):
        await generator.generate_component_async("", sample_meal_for_context)


@pytest.mark.parametrize(
    "api_response_text, expected_error_message",
    ERROR_SCENARIOS,
)
@patch("src.meal_generator.generator.genai")
def test_generate_component_error_scenarios(
    mock_genai: MagicMock,
    api_response_text: str,
    expected_error_message: str,
    sample_meal_for_context: Meal,
):
    """Tests that various invalid API responses raise MealGenerationError during component generation."""
    mock_response = MagicMock()
    mock_response.text = api_response_text
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response

    generator = MealGenerator(api_key="dummy_key")

    with pytest.raises(MealGenerationError, match=expected_error_message):
        generator.generate_component("some component", sample_meal_for_context)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "api_response_text, expected_error_message",
    ERROR_SCENARIOS,
)
@patch("src.meal_generator.generator.genai")
async def test_generate_component_async_error_scenarios(
    mock_genai: MagicMock,
    api_response_text: str,
    expected_error_message: str,
    sample_meal_for_context: Meal,
):
    """Tests invalid API responses for async component generation."""
    mock_async_response = MagicMock()
    mock_async_response.text = api_response_text
    mock_genai.Client.return_value.aio.models.generate_content = AsyncMock(
        return_value=mock_async_response
    )
    generator = MealGenerator(api_key="dummy_key")
    with pytest.raises(MealGenerationError, match=expected_error_message):
        await generator.generate_component_async(
            "some component", sample_meal_for_context
        )

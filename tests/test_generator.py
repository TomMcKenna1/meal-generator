import pytest
import json
from unittest.mock import AsyncMock, patch
from src.meal_generator.generator import MealGenerator, MealGenerationError
from src.meal_generator.meal import Meal
from src.meal_generator.meal_component import MealComponent


@pytest.fixture
def mock_identification_response() -> str:
    """Provides a valid JSON response for the identification step."""
    return json.dumps(
        {
            "status": "ok",
            "result": {
                "components": [
                    {
                        "query": "Scrambled Eggs",
                        "brand": None,
                        "user_specified_quantity": "2 large",
                    },
                    {
                        "query": "Whole Wheat Toast",
                        "brand": "Hovis",
                        "user_specified_quantity": "2 slices",
                    },
                ]
            },
        }
    )


@pytest.fixture
def mock_meal_synthesis_response() -> str:
    """Provides a valid JSON response for the meal synthesis step."""
    return json.dumps(
        {
            "status": "ok",
            "result": {
                "name": "Scrambled Eggs on Toast",
                "description": "A classic breakfast dish.",
                "type": "meal",
                "components": [
                    {
                        "name": "Scrambled Eggs",
                        "quantity": 2.0,
                        "metric": "large eggs",
                        "total_weight": 120.0,
                        "type": "food",
                        "nutrient_profile": {
                            "energy": 180.0,
                            "fats": 14.0,
                            "saturated_fats": 5.0,
                            "carbohydrates": 1.0,
                            "sugars": 1.0,
                            "fibre": 0.0,
                            "protein": 15.0,
                            "salt": 0.2,
                            "data_source": "estimated_model",
                        },
                    }
                ],
            },
        }
    )


@pytest.fixture
def mock_component_synthesis_response() -> str:
    """Provides a valid JSON response for the component list synthesis step."""
    return json.dumps(
        {
            "status": "ok",
            "result": {
                "components": [
                    {
                        "name": "Olive Oil",
                        "quantity": 1.0,
                        "metric": "tbsp",
                        "total_weight": 14.0,
                        "type": "food",
                        "nutrient_profile": {
                            "energy": 120.0,
                            "fats": 14.0,
                            "saturated_fats": 2.0,
                            "carbohydrates": 0.0,
                            "sugars": 0.0,
                            "fibre": 0.0,
                            "protein": 0.0,
                            "salt": 0.0,
                            "data_source": "retrieved_api",
                        },
                    }
                ]
            },
        }
    )


# --- ASYNC GENERATION TESTS ---


@pytest.mark.asyncio
@patch("src.meal_generator.generator.Retriever.process_components_concurrently")
@patch("src.meal_generator.generator.MealGenerator._call_ai_model_async")
async def test_generate_meal_async_success(
    mock_call_ai: AsyncMock,
    mock_retriever: AsyncMock,
    mock_identification_response: str,
    mock_meal_synthesis_response: str,
):
    """Tests a successful end-to-end asynchronous meal generation pipeline."""
    mock_call_ai.side_effect = [
        mock_identification_response,
        mock_meal_synthesis_response,
    ]
    mock_retriever.return_value = [{"user_query": "Scrambled Eggs"}]

    generator = MealGenerator(api_key="dummy")
    meal = await generator.generate_meal_async("some query")

    assert mock_call_ai.call_count == 2
    mock_retriever.assert_awaited_once()
    assert isinstance(meal, Meal)
    assert meal.name == "Scrambled Eggs on Toast"


@pytest.mark.asyncio
@patch("src.meal_generator.generator.Retriever.process_components_concurrently")
@patch("src.meal_generator.generator.MealGenerator._call_ai_model_async")
async def test_generate_component_async_success(
    mock_call_ai: AsyncMock,
    mock_retriever: AsyncMock,
    mock_identification_response: str,
    mock_component_synthesis_response: str,
):
    """Tests a successful end-to-end async component generation pipeline."""
    mock_call_ai.side_effect = [
        mock_identification_response,
        mock_component_synthesis_response,
    ]
    mock_retriever.return_value = [{"user_query": "Olive Oil"}]

    generator = MealGenerator(api_key="dummy")
    components = await generator.generate_component_async("some query")

    assert mock_call_ai.call_count == 2
    mock_retriever.assert_awaited_once()
    assert isinstance(components, list)
    assert len(components) == 1
    assert isinstance(components[0], MealComponent)
    assert components[0].name == "Olive Oil"


@pytest.mark.asyncio
@patch("src.meal_generator.generator.MealGenerator._call_ai_model_async")
async def test_generate_async_identification_fails(mock_call_ai: AsyncMock):
    """Tests that the pipeline fails if the first AI call (identification) fails."""
    mock_call_ai.return_value = '{"status": "bad_input"}'
    generator = MealGenerator(api_key="dummy")
    with pytest.raises(
        MealGenerationError, match="Input was determined to be malicious"
    ):
        await generator.generate_meal_async("some query")


@pytest.mark.asyncio
@patch("src.meal_generator.generator.Retriever.process_components_concurrently")
@patch("src.meal_generator.generator.MealGenerator._call_ai_model_async")
async def test_generate_async_synthesis_fails(
    mock_call_ai: AsyncMock,
    mock_retriever: AsyncMock,
    mock_identification_response: str,
):
    """Tests that the pipeline fails if the second AI call (synthesis) fails."""
    mock_call_ai.side_effect = [mock_identification_response, '{"status": "bad_input"}']
    mock_retriever.return_value = []

    generator = MealGenerator(api_key="dummy")
    with pytest.raises(
        MealGenerationError, match="Input was determined to be malicious"
    ):
        await generator.generate_meal_async("some query")

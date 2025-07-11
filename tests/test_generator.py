import pytest
import json
from unittest.mock import patch, MagicMock
from src.meal_generator.generator import MealGenerator, MealGenerationError
from src.meal_generator.meal import Meal

@pytest.fixture
def valid_api_response() -> dict:
    """Provides a valid, structured API response."""
    return {
        "status": "ok",
        "meal": {
            "name": "Scrambled Eggs on Toast",
            "description": "A classic breakfast dish.",
            "components": [
                {
                    "name": "Scrambled Eggs",
                    "brand": None,
                    "quantity": "2 large",
                    "totalWeight": 120.0,
                    "nutrientProfile": {"energy": 180, "protein": 15},
                },
                {
                    "name": "Whole Wheat Toast",
                    "brand": "Hovis",
                    "quantity": "2 slices",
                    "totalWeight": 60.0,
                    "nutrientProfile": {"energy": 160, "protein": 8, "containsGluten": True},
                },
            ],
        }
    }

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
    assert meal.nutrient_profile.energy == 340.0
    assert meal.nutrient_profile.protein == 23.0
    assert meal.nutrient_profile.contains_gluten is True

def test_generate_meal_empty_input():
    """Tests that an empty input string raises a ValueError."""
    generator = MealGenerator(api_key="dummy_key")
    with pytest.raises(ValueError, match="Natural language string cannot be empty for meal generation."):
        generator.generate_meal("")

@pytest.mark.parametrize(
    "api_response_text, error_message",
    [
        ('{"status": "bad_input"}', "Input does not describe a meal"),
        ('{"status": "ok", "meal": null}', "Unexpected AI response"),
        ('{"status": "ok", "meal": {"components": [{"nutrientProfile": {"energy": "invalid"}}]}}', "Malformed nutrient or component data encountered"),
        ('{"data": "wrong_structure"}', "Unexpected AI response"),
        ("this is not json", "Failed to get or parse AI model response"),
    ],
)
@patch("src.meal_generator.generator.genai")
def test_generate_meal_error_scenarios(mock_genai: MagicMock, api_response_text, error_message):
    """Tests that various invalid API responses raise MealGenerationError."""
    mock_response = MagicMock()
    mock_response.text = api_response_text
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response

    generator = MealGenerator(api_key="dummy_key")

    with pytest.raises(MealGenerationError, match=error_message):
        generator.generate_meal("some meal")
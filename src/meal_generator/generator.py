import html
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from pydantic import ValidationError

from .meal import Meal
from .meal_component import MealComponent
from .nutrient_profile import NutrientProfile
from .models import MealGenerationStatus, MealResponse


class MealGenerationError(Exception):
    """Custom exception for errors during meal generation."""

    pass


class MealGenerator:
    """
    Generates a Meal object from a natural language string using a Generative AI model
    """

    _MODEL_NAME = "gemini-2.5-flash"
    _PROMPT_TEMPLATE = """
        You are an expert food and nutrition analyst. Your task is to analyze a natural language
        description of a meal and break it down into its constituent components. You must return
        a single, well-formed JSON object.

        Analyze the following meal description enclosed in <user_input> tags. If the description
        is not a meal or food item, return {{"status":"bad_input"}}: 
        
        <user_input>
        "{natural_language_string}"
        </user_input>

        Based on your analysis, provide the following information in a JSON structure:
        - A name for the meal.
        - A brief and concise description of the meal.
        - A list of all individual components of the meal.

        For each component, provide:
        - The name of the ingredient.
        - The brand (if specified, otherwise null).
        - The quantity as described in the text (e.g., "1 cup", "2 slices").
        - The total weight in grams (provide a reasonable estimate, e.g., 120.5).
        - A detailed nutrient profile.

        The nutrient profile for each component must include estimates for:
        - energy (in kcal)
        - fat (in grams)
        - saturatedFats (in grams)
        - carbohydrates (in grams)
        - sugars (in grams)
        - fibre (in grams)
        - protein (in grams)
        - salt (in grams)
        - Allergen and sensitivity information (as booleans):
          - containsDairy, containsHighDairy
          - containsGluten, containsHighGluten
          - containsHistamines, containsHighHistamines
          - containsSulphites, containsHighSulphites
          - containsSalicylates, containsHighSalicylates
          - containsCapsaicin, containsHighCapsaicin
        - Processing level (as booleans):
          - isProcessed
          - isUltraProcessed
        """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the MealGenerator.

        Args:
            api_key (str, optional): The API key for accessing the Generative AI model.
                                     If not provided, it's expected to be set as an
                                     environment variable (e.g., GEMINI_API_KEY).
        """
        if api_key:
            self._genai_client = genai.Client(api_key=api_key)
        else:
            # Infer API from environment variable if not provided
            self._genai_client = genai.Client()

    def _create_prompt(self, natural_language_string: str) -> str:
        """
        Constructs the detailed prompt for the Generative AI model.

        Args:
            natural_language_string (str): The natural language description of the meal.

        Returns:
            str: The formatted prompt string.
        """
        # Escape tags to prevent prompt injection
        return self._PROMPT_TEMPLATE.format(
            natural_language_string=html.escape(natural_language_string)
        )

    def _call_ai_model(self, prompt: str) -> Dict[str, Any]:
        """
        Calls the Generative AI model with the given prompt and parses the JSON response.

        Args:
            prompt (str): The prompt to send to the AI model.

        Returns:
            Dict[str, Any]: The parsed JSON response from the AI model.

        Raises:
            MealGenerationError: If there's an error communicating with the AI model,
                                 or if the response is not valid JSON.
        """
        try:
            response = self._genai_client.models.generate_content(
                model=self._MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                    ],
                    response_mime_type="application/json",
                    response_schema=MealResponse,
                ),
            )
            return response.text
        except Exception as e:
            raise MealGenerationError(
                f"An unexpected error occurred during AI model interaction: {e}"
            ) from e

    def generate_meal(self, natural_language_string: str) -> Meal:
        """
        Takes a natural language string, sends it to the Generative AI model,
        and returns a structured Meal object.

        Args:
            natural_language_string (str): A natural language description of the meal
                                           (e.g., "A classic cheeseburger with fries").

        Returns:
            Meal: An object representing the generated meal with its components and
                  aggregated nutrient profile.

        Raises:
            ValueError: If the input natural language string is empty.
            MealGenerationError: If there's any failure in the generation process,
                                 such as API communication issues, invalid JSON response,
                                 or malformed data.
        """
        if not natural_language_string:
            raise ValueError(
                "Natural language string cannot be empty for meal generation."
            )

        prompt = self._create_prompt(natural_language_string)
        json_response_string = self._call_ai_model(prompt)
        try:
            pydantic_response = MealResponse.model_validate_json(json_response_string)
            if pydantic_response.status == MealGenerationStatus.BAD_INPUT:
                raise MealGenerationError("Input was determined to not be a meal.")
            if (
                pydantic_response.status == MealGenerationStatus.OK
                and pydantic_response.meal
            ):
                return Meal.from_pydantic(pydantic_response.meal)
            raise MealGenerationError(
                "AI response status was 'ok' but no meal data was provided."
            )
        except ValidationError as e:
            raise MealGenerationError(f"AI response failed validation: {e}") from e
        except Exception as e:
            raise MealGenerationError(f"Failed to process the AI response: {e}") from e

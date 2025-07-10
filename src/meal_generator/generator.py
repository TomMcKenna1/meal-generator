import html
import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from .meal import Meal
from .meal_component import MealComponent
from .nutrient_profile import NutrientProfile


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

        Here is the required JSON format:
        {{
          "status": "ok"
          "meal": {{
            "name": "...",
            "description": "...",
            "components": [
              {{
                "name": "...",
                "brand": null,
                "quantity": "...",
                "totalWeight": ...,
                "nutrientProfile": {{
                  "energy": ...,
                  "fat": ...,
                  "saturatedFats": ...,
                  "carbohydrates": ...,
                  "sugars": ...,
                  "fibre": ...,
                  "protein": ...,
                  "salt": ...,
                  "containsDairy": false,
                  "containsHighDairy": false,
                  "containsGluten": false,
                  "containsHighGluten": false,
                  "containsHistamines": false,
                  "containsHighHistamines": false,
                  "containsSulphites": false,
                  "containsHighSulphites": false,
                  "containsSalicylates": false,
                  "containsHighSalicylates": false,
                  "containsCapsaicin": false,
                  "containsHighCapsaicin": false,
                  "isProcessed": false,
                  "isUltraProcessed": false
                }}
              }}
            ]
          }}
        }}

        Return only the JSON object, with no additional text or explanations.
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
                    ]
                ),
            )
            raw_text = response.text
            cleaned_text = (
                raw_text.strip().replace("```json", "").replace("```", "").strip()
            )
            return json.loads(cleaned_text)
        except (
            ValueError,
            json.JSONDecodeError,
        ) as e:
            raise MealGenerationError(
                f"Failed to get or parse AI model response: {e}"
            ) from e
        except Exception as e:
            raise MealGenerationError(
                f"An unexpected error occurred during AI model interaction: {e}"
            ) from e

    def _parse_meal_data(self, meal_data: Dict[str, Any]) -> Meal:
        """
        Parses the raw meal data dictionary from the AI response into a Meal object.

        Args:
            meal_data (Dict[str, Any]): The dictionary containing meal and component data.

        Returns:
            Meal: A fully constructed Meal object.

        Raises:
            MealGenerationError: If essential data is missing or malformed in the parsed data.
        """
        component_list: List[MealComponent] = []
        for component_data in meal_data.get("components", []):
            try:
                nutrient_data = component_data.get("nutrientProfile", {})
                nutrient_profile = NutrientProfile(
                    energy=nutrient_data.get("energy", 0.0),
                    fats=nutrient_data.get("fat", 0.0),
                    saturated_fats=nutrient_data.get("saturatedFats", 0.0),
                    carbohydrates=nutrient_data.get("carbohydrates", 0.0),
                    sugars=nutrient_data.get("sugars", 0.0),
                    fibre=nutrient_data.get("fibre", 0.0),
                    protein=nutrient_data.get("protein", 0.0),
                    salt=nutrient_data.get("salt", 0.0),
                    contains_dairy=nutrient_data.get("containsDairy", False),
                    contains_high_dairy=nutrient_data.get("containsHighDairy", False),
                    contains_gluten=nutrient_data.get("containsGluten", False),
                    contains_high_gluten=nutrient_data.get("containsHighGluten", False),
                    contains_histamines=nutrient_data.get("containsHistamines", False),
                    contains_high_histamines=nutrient_data.get(
                        "containsHighHistamines", False
                    ),
                    contains_sulphites=nutrient_data.get("containsSulphites", False),
                    contains_high_sulphites=nutrient_data.get(
                        "containsHighSulphites", False
                    ),
                    contains_salicylates=nutrient_data.get(
                        "containsSalicylates", False
                    ),
                    contains_high_salicylates=nutrient_data.get(
                        "containsHighSalicylates", False
                    ),
                    contains_capsaicin=nutrient_data.get("containsCapsaicin", False),
                    contains_high_capsaicin=nutrient_data.get(
                        "containsHighCapsaicin", False
                    ),
                    is_processed=nutrient_data.get("isProcessed", False),
                    is_ultra_processed=nutrient_data.get("isUltraProcessed", False),
                )
                meal_component = MealComponent(
                    name=component_data.get("name", "Unknown Component"),
                    brand=component_data.get("brand"),
                    quantity=component_data.get("quantity", "N/A"),
                    total_weight=component_data.get("totalWeight", 0.0),
                    nutrient_profile=nutrient_profile,
                )
                component_list.append(meal_component)
            except TypeError as e:
                raise MealGenerationError(
                    f"Malformed nutrient or component data encountered: {e} in {component_data}"
                ) from e
            except Exception as e:
                raise MealGenerationError(
                    f"Error creating MealComponent or NutrientProfile: {e} in {component_data}"
                ) from e

        try:
            return Meal(
                name=meal_data.get("name", "Generated Meal"),
                description=meal_data.get("description", "A meal generated by AI."),
                component_list=component_list,
            )
        except ValueError as e:
            raise MealGenerationError(f"Invalid meal data received from AI: {e}") from e
        except Exception as e:
            raise MealGenerationError(f"Error constructing Meal object: {e}") from e

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
        raw_response_data = self._call_ai_model(prompt)

        generation_status = raw_response_data.get("status")
        meal_data = raw_response_data.get("meal")
        if generation_status == "ok" and meal_data:
            return self._parse_meal_data(meal_data)
        elif generation_status == "bad_input":
            raise MealGenerationError("Input does not describe a meal")
        raise MealGenerationError("Unexpected AI response")

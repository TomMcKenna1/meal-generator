import html
import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import ValidationError

from .mappable import _PydanticMappable
from .meal_component import MealComponent

from .meal import Meal
from .models import (
    _AIResponse,
    _GenerationStatus,
    _ComponentResponse,
    _MealResponse,
)


class MealGenerationError(Exception):
    """Custom exception for errors during meal generation."""

    pass


class MealGenerator:
    """
    Generates a Meal object from a natural language string using a Generative AI model
    """

    _MODEL_NAME = "gemini-2.5-flash"
    _PROMPT_TEMPLATE = """
        You are a sophisticated Food and Nutrition Intelligence Engine. Your primary goal is to analyze a natural language description of a meal and identify its main, user-level components, then return a single, well-formed JSON object.

        **You will be provided with a meal description and a country of origin in ISO 3166-2 format. This country is critical for your analysis, as food products, recipes, and nutritional standards vary internationally.**

        Your analysis must follow this Core Logic:

        1.  **Pre-defined and Branded Items:** If an item is a specific, well-known product (e.g., 'Dominos Mighty Meaty pizza'), treat it as a SINGLE component. DO NOT break it down into base ingredients. You must find the nutritional information for that specific product **as sold in the specified country**. For example, a 'Mighty Meaty' from the 'United Kingdom' will have different values than one from the 'United States'.

        2.  **Combo Meals:** If the item is a known 'combo meal' (e.g., 'KFC Zinger Tower Box Meal'), break it down into its main constituent ITEMS, **based on the menu for the specified country**. Do not break down these individual items any further.

        3.  **User-Described Meals:** If the user describes a meal by its main parts (e.g., 'pasta with single cream and lardons'), you MUST break it down into those specified components. **When estimating nutritional values for these generic components, base your estimates on typical food data and portion sizes for the specified country.**
        
        4.  **Meal Type Classification::** Based on the identified components and common cultural eating patterns in the specified country, classify the meal into one of four categories. Your choice must be one of: breakfast, lunch, dinner, or snack.

        Breakfast: Typically includes items like cereal, toast, eggs, porridge, or pastries.

        Lunch: Often consists of sandwiches, salads, soups, or lighter hot meals.

        Dinner: Usually the largest meal of the day, often hot and featuring complex dishes like roasts, curries, or large pasta meals.

        Snack: A small portion of food eaten between main meals, such as fruit, crisps, a chocolate bar, or yogurt.


        **Hierarchy:** Mirror the user's level of detail. If they name a single product, analyze that product within the given country context. If they list parts, analyze those parts using data relevant to that country.

        ---
        Meal Type Classification
        Based on the overall composition, portion size, and common cultural context of the provided item in the specified country, you must also classify it into one of three categories:

        meal: A substantial serving of food typically consumed at main mealtimes (e.g., breakfast, lunch, or dinner), often consisting of multiple components. Examples: 'a full English breakfast', 'roast chicken with vegetables', 'a large burrito'.

        snack: A smaller portion of food typically eaten between main meals. Examples: 'a bag of crisps', 'a chocolate bar', 'a single apple', 'a slice of cheese on toast'.

        beverage: An item that is primarily a drink. Examples: 'a can of Coke', 'a cup of coffee', 'orange juice', 'beer'. Note: A substantial, meal-replacement drink like a large smoothie could be classified as a snack or even a meal depending on its size and ingredients; use your discretion.
        
        ---

        Analyze the following meal information. If the description is not a meal or food item, return {{"status":"bad_input"}}:

        **<meal_description>**
        **"{natural_language_string}"**
        **</meal_description>**

        **<country_of_origin>**
        **"{country_ISO_3166_2}"**
        **</country_of_origin>**

        Based on your analysis and the Core Logic above, provide the following information in a JSON structure:
        - A name for the meal.
        - A brief and concise description of the meal.
        - A meal type classification, which must be one of the following strings: "snack", "meal", or "beverage".
        - A list of all individual components of the meal.

        For each component, provide:
        - The name of the ingredient.
        - The brand (if specified, otherwise null).
        - The quantity as described in the text (e.g., "1 cup", "2 slices", "1 regular portion").
        - The component's type, which must be one of the following strings: "food" or "beverage".
        - The total weight in grams (provide a reasonable estimate, e.g., 120.5).
        - A detailed nutrient profile.

        The nutrient profile for each component must include estimates for:
        - energy (in kcal)
        - fats (in grams)
        - saturatedFats (in grams)
        - carbohydrates (in grams)
        - sugars (in grams)
        - fibre (in grams)
        - protein (in grams)
        - salt (in grams)
        Allergen and sensitivity information (as booleans):
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
    _COMPONENT_PROMPT_TEMPLATE = """
        You are an expert food and nutrition analyst. Your task is to analyze a natural language
        description of a new food component and add it to an existing meal. You must return
        a single, well-formed JSON object representing the new component. If the description
        is not a meal or food item, return {{"status":"bad_input"}}: 

        The existing meal is:
        - Name: "{meal_name}"
        - Description: "{meal_description}"
        - Current Components: {existing_components}

        Analyze the new component description enclosed in <user_input> tags, considering the context of the existing meal.

        <user_input>
        "{natural_language_string}"
        </user_input>

        Based on your analysis, provide the following information for the new component in a JSON structure:
        - The name of the ingredient.
        - The brand (if specified, otherwise null).
        - The quantity as described in the text (e.g., "1 tbsp", "a handful").
        - The component's type, which must be one of the following strings: "food" or "beverage".
        - The total weight in grams (provide a reasonable estimate, e.g., 14.2).
        - A detailed nutrient profile.

        The nutrient profile for the component must include estimates for:
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

    def _create_model_config(self, **kwargs):
        return types.GenerateContentConfig(
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
            **kwargs,
        )

    def _create_prompt(self, natural_language_string: str, country_code: str) -> str:
        """
        Constructs the detailed prompt for the Generative AI model.

        Args:
            natural_language_string (str): The natural language description of the meal.

        Returns:
            str: The formatted prompt string.
        """
        # Escape tags to prevent prompt injection
        return self._PROMPT_TEMPLATE.format(
            natural_language_string=html.escape(natural_language_string),
            country_ISO_3166_2=html.escape(country_code),
        )

    def _create_component_prompt(
        self, natural_language_string: str, meal: Meal, country_code: str
    ) -> str:
        """
        Constructs the detailed prompt for generating a single component.
        """
        existing_components = json.dumps(
            [c.as_dict() for c in meal.component_list], indent=2
        )
        # Escape tags to prevent prompt injection
        return self._COMPONENT_PROMPT_TEMPLATE.format(
            meal_name=meal.name,
            meal_description=meal.description,
            existing_components=existing_components,
            natural_language_string=html.escape(natural_language_string),
            country_ISO_3166_2=html.escape(country_code),
        )

    def _call_ai_model(
        self, prompt: str, config: types.GenerateContentConfig
    ) -> Dict[str, Any]:
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
                config=config,
            )
            return response.text
        except Exception as e:
            raise MealGenerationError(
                f"An unexpected error occurred during AI model interaction: {e}"
            ) from e

    async def _call_ai_model_async(
        self, prompt: str, config: types.GenerateContentConfig
    ) -> str:
        """
        Calls the Generative AI model asynchronously with the given prompt and parses the JSON response.

        Args:
            prompt (str): The prompt to send to the AI model.

        Returns:
            Dict[str, Any]: The parsed JSON response from the AI model.

        Raises:
            MealGenerationError: If there's an error communicating with the AI model,
                                 or if the response is not valid JSON.
        """
        try:
            response = await self._genai_client.aio.models.generate_content(
                model=self._MODEL_NAME,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            raise MealGenerationError(
                f"An unexpected error occurred during async AI model interaction: {e}"
            ) from e

    def _process_response(
        self,
        return_model: _PydanticMappable,
        result_model: _AIResponse,
        json_response_string: str,
    ) -> Meal:
        """Helper to process the JSON response from ai model."""
        try:
            pydantic_response = result_model.model_validate_json(json_response_string)
            if pydantic_response.status == _GenerationStatus.BAD_INPUT:
                raise MealGenerationError("Input was determined to be malicious.")
            if (
                pydantic_response.status == _GenerationStatus.OK
                and pydantic_response.result
            ):
                return return_model.from_pydantic(pydantic_response.result)
            raise MealGenerationError(
                "AI response status was 'ok' but no object data was provided."
            )
        except ValidationError as e:
            raise MealGenerationError(f"AI response failed validation: {e}") from e
        except Exception as e:
            raise MealGenerationError(f"Failed to process the AI response: {e}") from e

    def generate_meal(
        self, natural_language_string: str, country_code: str = "US"
    ) -> Meal:
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

        prompt = self._create_prompt(natural_language_string, country_code)
        config = self._create_model_config(response_schema=_MealResponse)
        json_response_string = self._call_ai_model(prompt, config)
        return self._process_response(Meal, _MealResponse, json_response_string)

    async def generate_meal_async(
        self, natural_language_string: str, country_code: str = "US"
    ) -> Meal:
        """
        Asynchronous version of generate_meal.

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
            raise ValueError("Natural language string cannot be empty.")
        prompt = self._create_prompt(natural_language_string, country_code)
        config = self._create_model_config(response_schema=_MealResponse)
        json_response_string = await self._call_ai_model_async(prompt, config)
        return self._process_response(Meal, _MealResponse, json_response_string)

    def generate_component(
        self, natural_language_string: str, meal: Meal, country_code: str = "US"
    ) -> MealComponent:
        """
        Generates a single MealComponent from a natural language string in the context of an existing meal.

        Args:
            natural_language_string (str): A natural language description of the component.
            meal (Meal): The existing meal to which the component will be added.

        Returns:
            MealComponent: The generated meal component.
        """
        if not natural_language_string:
            raise ValueError("Natural language string cannot be empty.")
        prompt = self._create_component_prompt(
            natural_language_string, meal, country_code
        )
        config = self._create_model_config(response_schema=_ComponentResponse)
        json_response_string = self._call_ai_model(prompt, config)
        return self._process_response(
            MealComponent, _ComponentResponse, json_response_string
        )

    async def generate_component_async(
        self, natural_language_string: str, meal: Meal, country_code: str = "US"
    ) -> MealComponent:
        """
        Asynchronous version of generate_component.

        Args:
            natural_language_string (str): A natural language description of the component.
            meal (Meal): The existing meal to which the component will be added.

        Returns:
            MealComponent: The generated meal component.
        """
        if not natural_language_string:
            raise ValueError("Natural language string cannot be empty.")
        prompt = self._create_component_prompt(
            natural_language_string, meal, country_code
        )
        config = self._create_model_config(response_schema=_ComponentResponse)
        json_response_string = await self._call_ai_model_async(prompt, config)
        return self._process_response(
            MealComponent, _ComponentResponse, json_response_string
        )

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


import html
import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import ValidationError

from .mappable import _PydanticMappable
from .meal_component import MealComponent
from .meal import Meal
from .retriever import Retriever
from .prompts import IDENTIFY_COMPONENTS_PROMPT, SYNTHESIZE_MEAL_PROMPT
from .models import (
    _AIResponse,
    _GenerationStatus,
    _ComponentResponse,
    _MealResponse,
    _IdentificationResponse,
)


class MealGenerationError(Exception):
    pass


class MealGenerator:
    _MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self._genai_client = genai.Client(api_key=api_key)
        else:
            # Infer API from environment variable if not provided
            self._genai_client = genai.Client()
        self._retriever = Retriever()

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

    def _process_response(
        self, return_model: _PydanticMappable, result_model: _AIResponse, json_str: str
    ) -> Meal:
        try:
            pydantic_response = result_model.model_validate_json(json_str)
            if pydantic_response.status == _GenerationStatus.BAD_INPUT:
                raise MealGenerationError("Input was determined to be malicious.")
            if pydantic_response.result:
                return return_model.from_pydantic(pydantic_response.result)
            raise MealGenerationError("AI response status was 'ok' but no result was provided.")
        except ValidationError as e:
            raise MealGenerationError(f"AI response failed validation: {e}") from e
        except Exception as e:
            raise MealGenerationError(f"Failed to process AI response: {e}") from e
    
    def generate_meal(self, natural_language_string: str, country_code: str = "GB") -> Meal:
        if not natural_language_string:
            raise ValueError("Natural language string cannot be empty.")

        # === Step 1: Identify Components ===
        id_prompt = IDENTIFY_COMPONENTS_PROMPT.format(
            natural_language_string=html.escape(natural_language_string)
        )
        id_config = self._create_model_config(response_schema=_IdentificationResponse)
        id_response_str = self._call_ai_model(id_prompt, id_config)
        identified_components = _IdentificationResponse.model_validate_json(
            id_response_str
        ).components
        print(identified_components)
        # === Step 2: Retrieve Data for Each Component ===
        context_data = []
        for component in identified_components:
            retrieved_data = self._retriever.search_for_component(
                component.query, component.brand, country_code
            )
            if retrieved_data:
                context_data.append(retrieved_data)
            else:
                # Create a placeholder for the model to estimate
                context_data.append(
                    {
                        "name": component.query,
                        "brand": component.brand,
                        "data_source": "estimated_model", # Flag for estimation
                    }
                )

        # === Step 3: Augment and Generate Final Meal ===
        synth_prompt = SYNTHESIZE_MEAL_PROMPT.format(
            natural_language_string=html.escape(natural_language_string),
            country_ISO_3166_2=html.escape(country_code),
            context_data_json=json.dumps(context_data, indent=2),
        )
        synth_config = self._create_model_config(response_schema=_MealResponse)
        final_response_str = self._call_ai_model(synth_prompt, synth_config)

        return self._process_response(Meal, _MealResponse, final_response_str)

    # Async versions would follow the same logic using an async http client in the retriever
    # and async calls to the gemini client.

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

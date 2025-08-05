import html
import json
import logging
import dataclasses
import asyncio
from typing import Any, Optional, List, Type, TypeVar

from google import genai
from google.genai import types
from pydantic import ValidationError, BaseModel

from .meal import Meal
from .meal_component import MealComponent
from .retriever import Retriever
from .prompts import (
    IDENTIFY_AND_DECOMPOSE_PROMPT,
    HYBRID_SYNTHESIS_PROMPT,
    SYNTHESIZE_COMPONENTS_PROMPT,
)
from .models import (
    _AIResponse,
    _GenerationStatus,
    _MealResponse,
    _IdentificationResponse,
    _ComponentListResponse,
    _ComponentsIdentified,
    DataSource,
)

logger = logging.getLogger(__name__)

PydanticAIResponse = TypeVar("PydanticAIResponse", bound=_AIResponse)
PydanticResult = TypeVar("PydanticResult", bound=BaseModel)


class MealGenerationError(Exception):
    pass


class MealGenerator:
    _MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self._genai_client = genai.Client(api_key=api_key)
        else:
            self._genai_client = genai.Client()
        self._retriever = Retriever()
        logger.info(f"MealGenerator initialized for model '{self._MODEL_NAME}'.")

    def _create_model_config(self, **kwargs) -> types.GenerationConfig:
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

    async def _call_ai_model_async(
        self, prompt: str, config: types.GenerationConfig
    ) -> str:
        try:
            logger.debug("Sending async request to Generative AI model.")
            response = await self._genai_client.aio.models.generate_content(
                model=self._MODEL_NAME,
                contents=prompt,
                config=config,
            )
            logger.debug("Received async response from Generative AI model.")
            return response.text
        except Exception as e:
            logger.error("Async AI model interaction failed.", exc_info=True)
            raise MealGenerationError(
                f"An unexpected error occurred during async AI model interaction: {e}"
            ) from e

    def _process_response(
        self, pydantic_response_model: Type[PydanticAIResponse], json_str: str
    ) -> PydanticResult:
        """
        Validates and processes a JSON string against a Pydantic response model.
        Checks for bad input status and returns the validated result object.
        """
        try:
            pydantic_response = pydantic_response_model.model_validate_json(json_str)
            if pydantic_response.status == _GenerationStatus.BAD_INPUT:
                raise MealGenerationError("Input was determined to be malicious.")
            if pydantic_response.result:
                return pydantic_response.result
            raise MealGenerationError(
                "AI response status was 'ok' but no result was provided."
            )
        except ValidationError as e:
            raise MealGenerationError(f"AI response failed validation: {e}") from e
        except Exception as e:
            raise MealGenerationError(f"Failed to process AI response: {e}") from e

    async def generate_meal_async(
        self, natural_language_string: str, country_code: str = "GB"
    ) -> Meal:
        logger.info(
            f"Starting async meal generation for query: '{natural_language_string}'"
        )
        try:
            context_for_synthesis, _ = await self._identify_and_retrieve_async(
                natural_language_string, country_code
            )

            logger.info("Step 3: Synthesizing final meal object.")
            synth_prompt = HYBRID_SYNTHESIS_PROMPT.format(
                natural_language_string=html.escape(natural_language_string),
                country_ISO_3166_2=html.escape(country_code),
                context_data_json=json.dumps(context_for_synthesis, indent=2),
            )
            synth_config = self._create_model_config(response_schema=_MealResponse)
            final_response_str = await self._call_ai_model_async(
                synth_prompt, synth_config
            )

            pydantic_meal = self._process_response(_MealResponse, final_response_str)
            final_meal = Meal.from_pydantic(pydantic_meal)

            self._post_process_meal(final_meal, context_for_synthesis)
            logger.info("Successfully generated final meal object.")
            return final_meal
        except Exception as e:
            logger.error("Async meal generation pipeline failed.", exc_info=True)
            raise e

    def generate_component(
        self, natural_language_string: str, country_code: str = "GB"
    ) -> List[MealComponent]:
        """Synchronous wrapper for generate_component_async."""
        logger.info("Running generate_component synchronously.")
        return asyncio.run(
            self.generate_component_async(natural_language_string, country_code)
        )

    async def generate_component_async(
        self, natural_language_string: str, country_code: str = "GB"
    ) -> List[MealComponent]:
        """Generates a list of MealComponents from a natural language string."""
        logger.info(
            f"Starting async component generation for query: '{natural_language_string}'"
        )
        try:
            context_for_synthesis, _ = await self._identify_and_retrieve_async(
                natural_language_string, country_code
            )

            logger.info("Step 3: Synthesizing new component object(s).")
            synth_prompt = SYNTHESIZE_COMPONENTS_PROMPT.format(
                natural_language_string=html.escape(natural_language_string),
                country_ISO_3166_2=html.escape(country_code),
                context_data_json=json.dumps(context_for_synthesis, indent=2),
            )
            synth_config = self._create_model_config(
                response_schema=_ComponentListResponse
            )
            final_response_str = await self._call_ai_model_async(
                synth_prompt, synth_config
            )

            pydantic_result = self._process_response(
                _ComponentListResponse, final_response_str
            )
            final_components = [
                MealComponent.from_pydantic(c) for c in pydantic_result.components
            ]

            self._post_process_components(final_components, context_for_synthesis)
            logger.info(
                f"Successfully generated {len(final_components)} new component(s)."
            )
            return final_components
        except Exception as e:
            logger.error("Async component generation pipeline failed.", exc_info=True)
            raise e

    async def _identify_and_retrieve_async(
        self, natural_language_string: str, country_code: str
    ) -> tuple[list, list]:
        """Helper to run the shared identification and retrieval steps."""
        logger.info("Step 1: Identifying and decomposing components.")
        id_prompt = IDENTIFY_AND_DECOMPOSE_PROMPT.format(
            natural_language_string=html.escape(natural_language_string)
        )
        id_config = self._create_model_config(response_schema=_IdentificationResponse)
        id_response_str = await self._call_ai_model_async(id_prompt, id_config)

        pydantic_result: _ComponentsIdentified = self._process_response(
            _IdentificationResponse, id_response_str
        )
        identified_components = pydantic_result.components

        logger.info(
            f"Identified {len(identified_components)} individual components to process."
        )

        logger.info("Step 2: Retrieving context for all components concurrently.")
        context_for_synthesis = await self._retriever.process_components_concurrently(
            identified_components, country_code
        )
        logger.info(
            f"Context retrieval complete. Found data for {len(context_for_synthesis)} components."
        )
        return context_for_synthesis, identified_components

    def _post_process_meal(self, meal: Meal, context: list):
        """Helper to assign data sources to a full meal object."""
        logger.info(
            "Post-processing: Assigning deterministic data sources to final components."
        )
        data_source_map = {
            item.get("user_query"): item.get("data_source") for item in context
        }
        for component in meal.component_list:
            source_str = data_source_map.get(component.name)
            if source_str:
                source_enum = DataSource(source_str)
                updated_profile = dataclasses.replace(
                    component.nutrient_profile, data_source=source_enum
                )
                component.nutrient_profile = updated_profile
        meal.nutrient_profile = meal._calculate_aggregate_nutrients()

    def _post_process_components(self, components: List[MealComponent], context: list):
        """Helper to assign data sources to a list of components."""
        data_source_map = {
            item.get("user_query"): item.get("data_source") for item in context
        }
        for component in components:
            source = data_source_map.get(component.name)
            if source:
                updated_profile = dataclasses.replace(
                    component.nutrient_profile, data_source=source
                )
                component.nutrient_profile = updated_profile

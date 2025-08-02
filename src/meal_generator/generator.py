import html
import json
import logging
import dataclasses
import asyncio
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from pydantic import ValidationError

from .mappable import _PydanticMappable
from .meal import Meal
from .retriever import Retriever
from .prompts import IDENTIFY_AND_DECOMPOSE_PROMPT, HYBRID_SYNTHESIS_PROMPT
from .models import (
    _AIResponse,
    _GenerationStatus,
    _MealResponse,
    _IdentificationResponse,
    DataSource,
)

logger = logging.getLogger(__name__)


class MealGenerationError(Exception):
    pass


class MealGenerator:
    _MODEL_NAME = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None):
        """
        MODIFIED: Initializes the MealGenerator using the new genai.Client pattern.
        """
        if api_key:
            self._genai_client = genai.Client(api_key=api_key)
        else:
            # Infer API from environment variable if not provided
            self._genai_client = genai.Client()

        self._retriever = Retriever()
        logger.info(f"MealGenerator initialized for model '{self._MODEL_NAME}'.")

    def _create_model_config(self, **kwargs) -> types.GenerationConfig:
        """Creates the generation configuration for the AI model."""
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
        """Async version of the AI model call using the new client syntax."""
        try:
            logger.debug("Sending async request to Generative AI model.")
            # MODIFIED: Uses the new asynchronous client method.
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
        self, return_model: _PydanticMappable, result_model: _AIResponse, json_str: str
    ) -> Meal:
        """Helper to process and validate the JSON response from the AI model."""
        try:
            pydantic_response = result_model.model_validate_json(json_str)
            if pydantic_response.status == _GenerationStatus.BAD_INPUT:
                raise MealGenerationError("Input was determined to be malicious.")
            if pydantic_response.result:
                return return_model.from_pydantic(pydantic_response.result)
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
        """
        Generates a Meal using the fully asynchronous hybrid RAG pipeline.
        """
        if not natural_language_string:
            raise ValueError("Natural language string cannot be empty.")

        logger.info(
            f"Starting async meal generation for query: '{natural_language_string}'"
        )

        try:
            # Step 1: Identify and Decompose Components
            logger.info("Step 1: Identifying and decomposing components.")
            id_prompt = IDENTIFY_AND_DECOMPOSE_PROMPT.format(
                natural_language_string=html.escape(natural_language_string)
            )
            id_config = self._create_model_config(
                response_schema=_IdentificationResponse
            )
            id_response_str = await self._call_ai_model_async(id_prompt, id_config)
            identified_components = _IdentificationResponse.model_validate_json(
                id_response_str
            ).components
            logger.info(
                f"Identified {len(identified_components)} individual components to process."
            )

            # Step 2: Build Context Concurrently
            logger.info("Step 2: Retrieving context for all components concurrently.")
            context_for_synthesis = (
                await self._retriever.process_components_concurrently(
                    identified_components, country_code
                )
            )
            logger.info(
                f"Context retrieval complete. Found data for {len(context_for_synthesis)} components."
            )

            # Step 3: Synthesize Final Meal
            logger.info("Step 3: Synthesizing final meal object.")
            context_data_json = json.dumps(context_for_synthesis, indent=2)
            synth_prompt = HYBRID_SYNTHESIS_PROMPT.format(
                natural_language_string=html.escape(natural_language_string),
                country_ISO_3166_2=html.escape(country_code),
                context_data_json=context_data_json,
            )
            synth_config = self._create_model_config(response_schema=_MealResponse)
            final_response_str = await self._call_ai_model_async(
                synth_prompt, synth_config
            )

            final_meal = self._process_response(Meal, _MealResponse, final_response_str)

            # Step 4: Post-processing
            logger.info(
                "Step 4: Assigning deterministic data sources to final components."
            )
            data_source_map = {
                item.get("user_query"): item.get("data_source")
                for item in context_for_synthesis
            }
            for component in final_meal.component_list:
                # Use the original component query to find its determined data source
                source = data_source_map.get(component.name, DataSource.ESTIMATED_MODEL)
                updated_profile = dataclasses.replace(
                    component.nutrient_profile, data_source=source
                )
                component.nutrient_profile = updated_profile

            final_meal.nutrient_profile = final_meal._calculate_aggregate_nutrients()
            logger.info("Successfully generated final meal object.")

            return final_meal

        except Exception as e:
            logger.error("Async meal generation pipeline failed.", exc_info=True)
            raise e

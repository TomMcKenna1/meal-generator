# in retriever.py

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional


class Retriever:
    """Handles fetching and formatting data from the Open Food Facts API asynchronously."""

    def __init__(self):
        self._api_url = "https://world.openfoodfacts.org/cgi/search.pl"

    async def _get_products_async(
        self, session: aiohttp.ClientSession, query: str, country_code: str, count: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Async internal method to call the API with a descriptive query."""
        country_name = "United Kingdom" if country_code == "GB" else country_code
        params = {
            "search_terms": query.strip(),
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": count,
            "tagtype_0": "countries",
            "tag_contains_0": "contains",
            "tag_0": country_name,
        }

        try:
            async with session.get(self._api_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("products") if data.get("count", 0) > 0 else None
        except aiohttp.ClientError:
            # In production, you might want more specific error handling or logging here.
            return None

    def _format_100g_payload(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Formats a product to provide only the raw per-100g data and source URL."""
        # This synchronous helper method remains the same as before.
        nutriments = product.get("nutriments", {})

        def _get(key, default=None):
            return (
                nutriments.get(key)
                if isinstance(nutriments.get(key), (int, float))
                else default
            )

        nutrient_data_100g = {
            "energy": _get("energy-kcal_100g"),
            "fats": _get("fat_100g"),
            "saturatedFats": _get("saturated-fat_100g"),
            "carbohydrates": _get("carbohydrates_100g"),
            "sugars": _get("sugars_100g"),
            "fibre": _get("fiber_100g", 0.0),
            "protein": _get("proteins_100g"),
            "salt": _get("salt_100g"),
        }
        if any(
            nutrient_data_100g[key] is None
            for key in ["energy", "fats", "carbohydrates", "protein"]
        ):
            return None
        return {
            "found_product_name": product.get("product_name"),
            "found_brand": product.get("brands"),
            "data_source": "retrieved_api",
            "source_url": product.get("url"),
            "nutrients_per_100g": nutrient_data_100g,
        }

    async def _process_single_component(
        self,
        session: aiohttp.ClientSession,
        component: Dict[str, Any],
        country_code: str,
    ) -> Dict[str, Any]:
        """
        Processes one component through the full retrieval logic (exact then contextual).
        """
        query = component.query
        brand = component.brand
        placeholder = {
            "user_query": query,
            "user_brand": brand,
            "user_specified_quantity": component.user_specified_quantity,
        }

        # Layer 1: Attempt exact match (if brand exists)
        if brand:
            search_query = f"{brand} {query}"
            products = await self._get_products_async(
                session, search_query, country_code, count=3
            )
            if products:
                normalized_query_brand = brand.strip().lower()
                for product in products:
                    result_brand_str = product.get("brands")
                    if (
                        result_brand_str
                        and normalized_query_brand in result_brand_str.strip().lower()
                    ):
                        formatted_payload = self._format_100g_payload(product)
                        if formatted_payload:
                            placeholder.update(formatted_payload)
                            return placeholder

        # Layer 2: No exact match, find contextual examples
        context_products = await self._get_products_async(
            session, query, country_code, count=3
        )
        contextual_examples = []
        if context_products:
            for product in context_products:
                payload = {
                    "name": product.get("product_name"),
                    "brand": product.get("brands"),
                    "weight_g": product.get("nutriments", {}).get("serving_quantity")
                    or 100.0,
                    "energy_kcal": product.get("nutriments", {}).get(
                        "energy-kcal_serving"
                    )
                    or product.get("nutriments", {}).get("energy-kcal_100g"),
                }
                if payload["name"] and payload["energy_kcal"]:
                    contextual_examples.append(payload)

        if contextual_examples:
            placeholder["data_source"] = "estimated_with_context"
            placeholder["contextual_examples"] = contextual_examples
        else:
            placeholder["data_source"] = "estimated_model"

        return placeholder

    async def process_components_concurrently(
        self, components: List[Dict[str, Any]], country_code: str
    ) -> List[Dict[str, Any]]:
        """
        Top-level method to process all identified components concurrently.
        """
        # Production-ready safety: Use a timeout for the entire session.
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [
                self._process_single_component(session, component, country_code)
                for component in components
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out potential exceptions from failed requests, though aiohttp handles most.
        return [res for res in results if not isinstance(res, Exception)]

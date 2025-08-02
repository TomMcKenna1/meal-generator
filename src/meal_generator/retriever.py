# in retriever.py

import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class Retriever:
    """Handles fetching and formatting data from the Open Food Facts API."""

    def __init__(self):
        self._api_url = "https://world.openfoodfacts.org/cgi/search.pl"

    def _get_products(
        self, query: str, brand: Optional[str], country_code: str, count: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Internal method to call the API."""
        search_terms = f"{brand} {query}" if brand else query

        # Convert country code to Open Food Facts tag format if needed
        # For simplicity, we assume common names work (e.g., "United Kingdom")
        # A mapping from ISO code to OFF name might be needed for production
        country_name = "United Kingdom" if country_code == "GB" else country_code

        params = {
            "search_terms": search_terms.strip(),
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": count,
            "tagtype_0": "countries",
            "tag_contains_0": "contains",
            "tag_0": country_name,
        }
        try:
            response = requests.get(self._api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("products") if data.get("count", 0) > 0 else None
        except requests.exceptions.RequestException:
            return None

    def _format_payload(self, product: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Formats a single product into the RAG JSON structure."""
        # This function contains the logic from our previous script to create the
        # RAG-optimized JSON payload for a single product.
        # (For brevity, this is a simplified version)
        nutriments = product.get("nutriments", {})

        def _get(key, default=None):
            return nutriments.get(key, default)

        # Map to _NutrientProfile Pydantic model structure
        nutrient_profile_data = {
            "energy": _get("energy-kcal_100g"),
            "fats": _get("fat_100g"),
            "saturatedFats": _get("saturated-fat_100g"),
            "carbohydrates": _get("carbohydrates_100g"),
            "sugars": _get("sugars_100g"),
            "fibre": _get("fiber_100g", 0.0),  # Default fiber to 0 if missing
            "protein": _get("proteins_100g"),
            "salt": _get("salt_100g"),
            "containsGluten": "en:gluten" in product.get("allergens_hierarchy", []),
            # ... other flags can be inferred from ingredients/tags ...
            "isUltraProcessed": product.get("nova_group") == 4,
            "dataSource": "retrieved_api",
        }
        # Filter out null values for required fields before returning
        for key in [
            "energy",
            "fats",
            "saturatedFats",
            "carbohydrates",
            "sugars",
            "protein",
            "salt",
        ]:
            if nutrient_profile_data[key] is None:
                # If a core nutrient is missing, we can't use this result
                return None

        component_data = {
            "name": product.get("product_name"),
            "brand": product.get("brands"),
            "quantity": product.get("serving_size", "100g"),
            "totalWeight": 100.0,  # Data is per 100g
            "type": (
                "beverage"
                if "beverages" in product.get("categories_tags", [])
                else "food"
            ),
            "nutrientProfile": nutrient_profile_data,
        }
        return component_data

    def search_for_component(
        self, query: str, brand: Optional[str], country_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Searches for a single best component match and returns it in a
        format ready for the synthesis prompt.
        """
        products = self._get_products(query, brand, country_code, count=3)
        if not products:
            return None

        # Find the first valid, formatted product
        for product in products:
            formatted_payload = self._format_payload(product, query)
            if formatted_payload:
                return formatted_payload
        return None

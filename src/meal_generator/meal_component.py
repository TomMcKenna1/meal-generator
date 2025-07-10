from typing import Optional
from .nutrient_profile import NutrientProfile

class MealComponent:
    """
    Represents a single component of a meal.
    """
    def __init__(self, name: str, quantity: str, total_weight: float,
                 nutrient_profile: NutrientProfile, brand: Optional[str] = None):
        self.name = name
        self.brand = brand
        self.quantity = quantity
        self.total_weight = total_weight
        self.nutrient_profile = nutrient_profile

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "brand": self.brand,
            "quantity": self.quantity,
            "totalWeight": self.total_weight,
            "nutrientProfile": self.nutrient_profile.as_dict(),
        }

    def __repr__(self) -> str:
        return f"<MealComponent(name='{self.name}', quantity='{self.quantity}')>"
from typing import Optional
from .nutrient_profile import NutrientProfile
from .models import Component


class MealComponent:
    """
    Represents a single component of a meal.
    """

    def __init__(
        self,
        name: str,
        quantity: str,
        total_weight: float,
        nutrient_profile: NutrientProfile,
        brand: Optional[str] = None,
    ):
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

    @classmethod
    def from_pydantic(cls, pydantic_component: Component) -> "MealComponent":
        """
        Factory method to create a MealComponent business object
        from its Pydantic data model representation.
        """
        nutrient_profile_object = NutrientProfile.from_pydantic(
            pydantic_component.nutrient_profile
        )

        return cls(
            name=pydantic_component.name,
            brand=pydantic_component.brand,
            quantity=pydantic_component.quantity,
            total_weight=pydantic_component.total_weight,
            nutrient_profile=nutrient_profile_object,
        )

    def to_pydantic(self) -> Component:
        """
        Converts the MealComponent business object into its
        Pydantic data model representation for serialization.
        """
        pydantic_nutrient_profile = self.nutrient_profile.to_pydantic()

        return Component(
            name=self.name,
            brand=self.brand,
            quantity=self.quantity,
            total_weight=self.total_weight,
            nutrient_profile=pydantic_nutrient_profile,
        )

    def __repr__(self) -> str:
        return f"<MealComponent(name='{self.name}', quantity='{self.quantity}')>"

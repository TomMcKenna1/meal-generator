from dataclasses import dataclass, asdict, field
from typing import Dict, Any
from .models import NutrientProfile as PydanticNutrientProfile


@dataclass(frozen=True, slots=True)
class NutrientProfile:
    """
    Holds the nutrient information and dietary properties for a meal or meal component.

    This class is immutable, meaning its state cannot be changed after creation.
    It uses Python's dataclasses for concise definition and provides methods for
    validation and serialization.

    Attributes:
        energy (float): Total energy in kilocalories (kcal). Must be non-negative.
        fats (float): Total fats in grams (g). Must be non-negative.
        saturated_fats (float): Saturated fats in grams (g). Must be non-negative.
        carbohydrates (float): Total carbohydrates in grams (g). Must be non-negative.
        sugars (float): Total sugars in grams (g). Must be non-negative.
        fibre (float): Total fibre in grams (g). Must be non-negative.
        protein (float): Total protein in grams (g). Must be non-negative.
        salt (float): Total salt in grams (g). Must be non-negative.
        contains_dairy (bool): True if the item contains dairy.
        contains_high_dairy (bool): True if the item contains a high amount of dairy.
        contains_gluten (bool): True if the item contains gluten.
        contains_high_gluten (bool): True if the item contains a high amount of gluten.
        contains_histamines (bool): True if the item contains histamines.
        contains_high_histamines (bool): True if the item contains a high amount of histamines.
        contains_sulphites (bool): True if the item contains sulphites.
        contains_high_sulphites (bool): True if the item contains a high amount of sulphites.
        contains_salicylates (bool): True if the item contains salicylates.
        contains_high_salicylates (bool): True if the item contains a high amount of salicylates.
        contains_capsaicin (bool): True if the item contains capsaicin.
        contains_high_capsaicin (bool): True if the item contains a high amount of capsaicin.
        is_processed (bool): True if the item is processed.
        is_ultra_processed (bool): True if the item is ultra-processed.
    """

    energy: float = field(default=0.0)
    fats: float = field(default=0.0)
    saturated_fats: float = field(default=0.0)
    carbohydrates: float = field(default=0.0)
    sugars: float = field(default=0.0)
    fibre: float = field(default=0.0)
    protein: float = field(default=0.0)
    salt: float = field(default=0.0)

    contains_dairy: bool = field(default=False)
    contains_high_dairy: bool = field(default=False)
    contains_gluten: bool = field(default=False)
    contains_high_gluten: bool = field(default=False)
    contains_histamines: bool = field(default=False)
    contains_high_histamines: bool = field(default=False)
    contains_sulphites: bool = field(default=False)
    contains_high_sulphites: bool = field(default=False)
    contains_salicylates: bool = field(default=False)
    contains_high_salicylates: bool = field(default=False)
    contains_capsaicin: bool = field(default=False)
    contains_high_capsaicin: bool = field(default=False)
    is_processed: bool = field(default=False)
    is_ultra_processed: bool = field(default=False)

    def as_dict(self) -> Dict[str, Any]:
        """
        Serializes the nutrient profile to a dictionary.

        Returns:
            dict: A dictionary representation of the nutrient profile.
        """
        return asdict(self)

    def __post_init__(self):
        numerical_fields = [
            "energy",
            "fats",
            "saturated_fats",
            "carbohydrates",
            "sugars",
            "fibre",
            "protein",
            "salt",
        ]
        for field_name in numerical_fields:
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"'{field_name}' must be a numeric value, got {type(value).__name__}."
                )
            if value < 0:
                raise ValueError(f"'{field_name}' cannot be negative. Got {value}.")
            object.__setattr__(self, field_name, float(value))

    @classmethod
    def from_pydantic(
        cls, pydantic_profile: PydanticNutrientProfile
    ) -> "NutrientProfile":
        """
        Factory method to create a NutrientProfile business object
        from its Pydantic data model representation.
        """
        return cls(**pydantic_profile.model_dump())

    def to_pydantic(self) -> PydanticNutrientProfile:
        """
        Converts the NutrientProfile business object into its
        Pydantic data model representation for serialization.
        """
        return PydanticNutrientProfile(**asdict(self))

    def __repr__(self) -> str:
        return (
            f"<NutrientProfile(energy={self.energy:.1f}kcal, protein={self.protein:.1f}g, "
            f"fats={self.fats:.1f}g, carbs={self.carbohydrates:.1f}g)>"
        )

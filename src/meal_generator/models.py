import enum
from typing import List, Optional
from pydantic import BaseModel, Field, AliasGenerator
from pydantic.config import ConfigDict


def to_camel(snake_case_str: str) -> str:
    """Convert a snake_case string to camelCase."""
    first, *others = snake_case_str.split("_")
    return first + "".join(word.capitalize() for word in others)


class MealGenerationStatus(enum.Enum):
    OK = "ok"
    BAD_INPUT = "bad_input"


class NutrientProfile(BaseModel):
    """
    Represents the nutrient profile of a meal component.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel, serialization_alias=to_camel
        ),
        populate_by_name=True,
    )

    energy: float
    fats: float
    saturated_fats: float
    carbohydrates: float
    sugars: float
    fibre: float
    protein: float
    salt: float
    contains_dairy: bool = False
    contains_high_dairy: bool = False
    contains_gluten: bool = False
    contains_high_gluten: bool = False
    contains_histamines: bool = False
    contains_high_histamines: bool = False
    contains_sulphites: bool = False
    contains_high_sulphites: bool = False
    contains_salicylates: bool = False
    contains_high_salicylates: bool = False
    contains_capsaicin: bool = False
    contains_high_capsaicin: bool = False
    is_processed: bool = False
    is_ultra_processed: bool = False


class Component(BaseModel):
    """
    Represents a component of a meal.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel, serialization_alias=to_camel
        ),
        populate_by_name=True,
    )

    name: str
    brand: Optional[str] = None
    quantity: str
    total_weight: float
    nutrient_profile: NutrientProfile


class Meal(BaseModel):
    """
    Represents a meal, including its components.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel, serialization_alias=to_camel
        ),
        populate_by_name=True,
    )
    name: str
    description: str
    components: List[Component]


class MealResponse(BaseModel):
    """
    Represents the top-level response for a meal query.
    """

    status: MealGenerationStatus
    meal: Optional[Meal] = None

import enum
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel
from pydantic.config import ConfigDict
from pydantic.alias_generators import to_camel


class _GenerationStatus(enum.Enum):
    OK = "ok"
    BAD_INPUT = "bad_input"


class MealType(enum.Enum):
    SNACK = "snack"
    MEAL = "meal"
    BEVERAGE = "beverage"


class ComponentType(enum.Enum):
    FOOD = "food"
    BEVERAGE = "beverage"


class DataSource(enum.Enum):
    """Specifies the origin of the nutritional data."""

    RETRIEVED_API = "retrieved_api"
    ESTIMATED_MODEL = "estimated_model"


class _NutrientProfile(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
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
    data_source: DataSource


class _Component(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    brand: Optional[str] = None
    quantity: str
    total_weight: float
    type: ComponentType
    nutrient_profile: _NutrientProfile


class _Meal(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    description: str
    type: MealType
    components: List[_Component]


# --- Models for the RAG Identification Step ---


class _IdentifiedComponent(BaseModel):
    """Represents a component identified for searching."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    query: str
    brand: Optional[str] = None


class _IdentificationResponse(BaseModel):
    """The expected response from the identification prompt."""

    components: List[_IdentifiedComponent]


# --- Generic AI Response Models ---

ResultT = TypeVar("ResultT", bound=BaseModel)


class _AIResponse(BaseModel, Generic[ResultT]):
    status: _GenerationStatus
    result: Optional[ResultT] = None


_MealResponse = _AIResponse[_Meal]
_ComponentResponse = _AIResponse[_Component]
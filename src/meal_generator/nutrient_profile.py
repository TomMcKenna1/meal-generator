from dataclasses import dataclass, asdict, field, fields
from typing import Dict, Any
from .models import _NutrientProfile, DataSource


@dataclass(frozen=True, slots=True)
class NutrientProfile:
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
    data_source: DataSource = field(default=DataSource.ESTIMATED_MODEL)

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["data_source"] = self.data_source.value
        return d

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
    def from_pydantic(cls, pydantic_profile: _NutrientProfile) -> "NutrientProfile":
        dumped_data = pydantic_profile.model_dump()
        if "data_source" in dumped_data and isinstance(dumped_data["data_source"], str):
            dumped_data["data_source"] = DataSource(dumped_data["data_source"])
        return cls(**dumped_data)

    def __add__(self, other: "NutrientProfile") -> "NutrientProfile":
        new_values = {}
        for f in fields(self):
            if f.name == "data_source":
                source_priority = {
                    DataSource.ESTIMATED_MODEL.value: 0,
                    DataSource.ESTIMATED_WITH_CONTEXT.value: 1,
                    DataSource.RETRIEVED_API.value: 2,
                }
                self_priority = source_priority[self.data_source.value]
                other_priority = source_priority[other.data_source.value]

                if self_priority < other_priority:
                    new_values[f.name] = self.data_source
                else:
                    new_values[f.name] = other.data_source
            elif isinstance(getattr(self, f.name), bool):
                new_values[f.name] = getattr(self, f.name) or getattr(other, f.name)
            elif isinstance(getattr(self, f.name), (int, float)):
                new_values[f.name] = getattr(self, f.name) + getattr(other, f.name)
        return NutrientProfile(**new_values)

    __radd__ = __add__

    def __repr__(self) -> str:
        return (
            f"<NutrientProfile(energy={self.energy:.1f}kcal, protein={self.protein:.1f}g, "
            f"fats={self.fats:.1f}g, carbs={self.carbohydrates:.1f}g, source={self.data_source.name})>"
        )

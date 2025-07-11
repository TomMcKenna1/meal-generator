import uuid
from typing import List, Dict, Any

from .meal_component import MealComponent
from .nutrient_profile import NutrientProfile
from .models import Meal as PydanticMeal


class Meal:
    """
    Represents a complete meal, composed of various components.

    Attributes:
        id (uuid.UUID): Unique identifier for the meal.
        name (str): The name of the meal.
        description (str): A description of the meal.
        component_list (List[MealComponent]): A list of components that make up the meal.
        nutrient_profile (NutrientProfile): The aggregated nutrient profile of the meal.
    """

    def __init__(
        self, name: str, description: str, component_list: List[MealComponent]
    ):
        if not name:
            raise ValueError("Meal name cannot be empty.")
        if not description:
            raise ValueError("Meal description cannot be empty.")
        if not component_list:
            raise ValueError("Meal must contain at least one component.")

        self.id: uuid.UUID = uuid.uuid4()
        self.name: str = name
        self.description: str = description
        self.component_list: List[MealComponent] = component_list
        self.nutrient_profile: NutrientProfile = self._calculate_aggregate_nutrients()

    def _calculate_aggregate_nutrients(self) -> NutrientProfile:
        """
        Calculates and returns the total nutrient profile for the meal from its components.
        This method aggregates both numerical nutrient values and boolean flags.
        """
        total_energy = sum(c.nutrient_profile.energy for c in self.component_list)
        total_fats = sum(c.nutrient_profile.fats for c in self.component_list)
        total_saturated_fats = sum(
            c.nutrient_profile.saturated_fats for c in self.component_list
        )
        total_carbohydrates = sum(
            c.nutrient_profile.carbohydrates for c in self.component_list
        )
        total_sugars = sum(c.nutrient_profile.sugars for c in self.component_list)
        total_fibre = sum(c.nutrient_profile.fibre for c in self.component_list)
        total_protein = sum(c.nutrient_profile.protein for c in self.component_list)
        total_salt = sum(c.nutrient_profile.salt for c in self.component_list)

        contains_dairy = any(
            c.nutrient_profile.contains_dairy for c in self.component_list
        )
        contains_high_dairy = any(
            c.nutrient_profile.contains_high_dairy for c in self.component_list
        )
        contains_gluten = any(
            c.nutrient_profile.contains_gluten for c in self.component_list
        )
        contains_high_gluten = any(
            c.nutrient_profile.contains_high_gluten for c in self.component_list
        )
        contains_histamines = any(
            c.nutrient_profile.contains_histamines for c in self.component_list
        )
        contains_high_histamines = any(
            c.nutrient_profile.contains_high_histamines for c in self.component_list
        )
        contains_sulphites = any(
            c.nutrient_profile.contains_sulphites for c in self.component_list
        )
        contains_high_sulphites = any(
            c.nutrient_profile.contains_high_sulphites for c in self.component_list
        )
        contains_salicylates = any(
            c.nutrient_profile.contains_salicylates for c in self.component_list
        )
        contains_high_salicylates = any(
            c.nutrient_profile.contains_high_salicylates for c in self.component_list
        )
        contains_capsaicin = any(
            c.nutrient_profile.contains_capsaicin for c in self.component_list
        )
        contains_high_capsaicin = any(
            c.nutrient_profile.contains_high_capsaicin for c in self.component_list
        )
        is_processed = any(c.nutrient_profile.is_processed for c in self.component_list)
        is_ultra_processed = any(
            c.nutrient_profile.is_ultra_processed for c in self.component_list
        )

        return NutrientProfile(
            energy=total_energy,
            fats=total_fats,
            saturated_fats=total_saturated_fats,
            carbohydrates=total_carbohydrates,
            sugars=total_sugars,
            fibre=total_fibre,
            protein=total_protein,
            salt=total_salt,
            contains_dairy=contains_dairy,
            contains_high_dairy=contains_high_dairy,
            contains_gluten=contains_gluten,
            contains_high_gluten=contains_high_gluten,
            contains_histamines=contains_histamines,
            contains_high_histamines=contains_high_histamines,
            contains_sulphites=contains_sulphites,
            contains_high_sulphites=contains_high_sulphites,
            contains_salicylates=contains_salicylates,
            contains_high_salicylates=contains_high_salicylates,
            contains_capsaicin=contains_capsaicin,
            contains_high_capsaicin=contains_high_capsaicin,
            is_processed=is_processed,
            is_ultra_processed=is_ultra_processed,
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "nutrient_profile": self.nutrient_profile.as_dict(),
            "components": [component.as_dict() for component in self.component_list],
        }

    def add_component(self, component: MealComponent):
        """
        Adds a new component to the meal.

        Args:
            component (MealComponent): The meal component to add.
        """
        self.component_list.append(component)
        self.nutrient_profile = self._calculate_aggregate_nutrients()

    def remove_component(self, component_id: uuid.UUID) -> bool:
        """
        Removes a component from the meal by its ID.

        Args:
            component_id (uuid.UUID): The ID of the component to remove.

        Returns:
            bool: True if the component was removed, False otherwise.
        """
        initial_count = len(self.component_list)
        self.component_list = [c for c in self.component_list if c.id != component_id]
        if len(self.component_list) < initial_count:
            self.nutrient_profile = self._calculate_aggregate_nutrients()
            return True
        return False

    def get_component_by_id(self, component_id: uuid.UUID) -> MealComponent | None:
        """
        Retrieves a meal component by its ID.

        Args:
            component_id (uuid.UUID): The ID of the component to retrieve.

        Returns:
            MealComponent | None: The found MealComponent object, or None if not found.
        """
        for component in self.component_list:
            if component.id == component_id:
                return component
        return None

    @classmethod
    def from_pydantic(cls, pydantic_meal: PydanticMeal) -> "Meal":
        """
        Factory method to create a business logic Meal object
        from a Pydantic Meal data model.
        """
        components = [MealComponent.from_pydantic(c) for c in pydantic_meal.components]
        return cls(
            name=pydantic_meal.name,
            description=pydantic_meal.description,
            component_list=components,
        )

    def to_pydantic(self) -> PydanticMeal:
        """
        Converts the business logic Meal object into its
        Pydantic representation for serialization.
        """
        pydantic_components = [c.to_pydantic() for c in self.component_list]
        return PydanticMeal(
            name=self.name, description=self.description, components=pydantic_components
        )

    def __repr__(self) -> str:
        return f"<Meal(id={self.id}, name='{self.name}', components={len(self.component_list)})>"

    def __str__(self) -> str:
        return f"Meal: {self.name} ({len(self.component_list)} components)"

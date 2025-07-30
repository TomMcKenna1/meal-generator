import uuid
from typing import List, Dict, Any, TYPE_CHECKING

from .mappable import _PydanticMappable
from .meal_component import MealComponent
from .nutrient_profile import NutrientProfile
from .models import _Meal, MealType

if TYPE_CHECKING:
    from .generator import MealGenerator


class DuplicateComponentIDError(Exception):
    """Raised when trying to add a component with an ID that already exists."""

    pass


class ComponentDoesNotExist(Exception):
    """Raised when trying to remove a component that does not exist."""

    pass


class Meal(_PydanticMappable):
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
        self,
        name: str,
        description: str,
        meal_type: MealType,
        component_list: List[MealComponent],
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
        self.type: MealType = meal_type
        self._components: dict[uuid.UUID, MealComponent] = {
            component.id: component for component in component_list
        }
        self.nutrient_profile: NutrientProfile = self._calculate_aggregate_nutrients()

    @property
    def component_list(self) -> list[MealComponent]:
        return list(self._components.values())

    def _calculate_aggregate_nutrients(self) -> NutrientProfile:
        """
        Calculates the total nutrient profile for the meal from its components.
        """
        return sum([c.nutrient_profile for c in self.component_list], NutrientProfile())

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "nutrient_profile": self.nutrient_profile.as_dict(),
            "components": [component.as_dict() for component in self.component_list],
        }

    def add_component(self, component: MealComponent):
        """
        Adds a new component to the meal.

        Args:
            component (MealComponent): The meal component to add.
        """
        if component.id in self._components:
            raise DuplicateComponentIDError(
                f"Component with id: {component.id} already exists"
            )
        self._components[component.id] = component
        self.nutrient_profile = self._calculate_aggregate_nutrients()

    def add_component_from_string(
        self, natural_language_string: str, meal_generator: "MealGenerator"
    ) -> "Meal":
        """
        Generates a new component from a natural language string and adds it to the meal.

        Args:
            natural_language_string (str): The natural language description of the component.
            meal_generator (MealGenerator): The meal generator to use for component creation.

        Returns:
            Meal: The modified meal with the new component.
        """
        new_component = meal_generator.generate_component(natural_language_string, self)
        self.add_component(new_component)
        return self

    async def add_component_from_string_async(
        self, natural_language_string: str, meal_generator: "MealGenerator"
    ) -> "Meal":
        """
        Generates a new component from a natural language string and adds it to the meal.

        Args:
            natural_language_string (str): The natural language description of the component.
            meal_generator (MealGenerator): The meal generator to use for component creation.

        Returns:
            Meal: The modified meal with the new component.
        """
        new_component = await meal_generator.generate_component_async(
            natural_language_string, self
        )
        self.add_component(new_component)
        return self

    def remove_component(self, component_id: uuid.UUID) -> None:
        """
        Removes a component from the meal by its ID.

        Args:
            component_id (uuid.UUID): The ID of the component to remove.

        Returns:
            bool: True if the component was removed, False otherwise.
        """
        if component_id not in self._components:
            raise ComponentDoesNotExist(f"Component id: {component_id} does not exist")
        del self._components[component_id]
        self.nutrient_profile = self._calculate_aggregate_nutrients()

    def get_component_by_id(self, component_id: uuid.UUID) -> MealComponent | None:
        """
        Retrieves a meal component by its ID.

        Args:
            component_id (uuid.UUID): The ID of the component to retrieve.

        Returns:
            MealComponent | None: The found MealComponent object, or None if not found.
        """
        return self._components.get(component_id)

    @classmethod
    def from_pydantic(cls, pydantic_meal: _Meal) -> "Meal":
        """
        Factory method to create a business logic Meal object
        from a Pydantic Meal data model.
        """
        components = [MealComponent.from_pydantic(c) for c in pydantic_meal.components]
        return cls(
            name=pydantic_meal.name,
            description=pydantic_meal.description,
            meal_type=pydantic_meal.type,
            component_list=components,
        )

    def __repr__(self) -> str:
        return f"<Meal(id={self.id}, name='{self.name}', components={len(self.component_list)})>"

    def __str__(self) -> str:
        return f"Meal: {self.name} ({len(self.component_list)} components)"

.. _meal-module:

****
meal
****

.. automodule:: meal_generator.meal
   :members:
   :undoc-members:
   :show-inheritance:

   .. autoclass:: Meal
      :members:
      :undoc-members:
      :show-inheritance:

      Represents a complete meal, composed of various components.

      .. attribute:: id
         :type: uuid.UUID

         Unique identifier for the meal.

      .. attribute:: name
         :type: str

         The name of the meal.

      .. attribute:: description
         :type: str

         A description of the meal.

      .. attribute:: component_list
         :type: List[MealComponent]

         A list of components that make up the meal.

      .. attribute:: nutrient_profile
         :type: NutrientProfile

         The aggregated nutrient profile of the meal.


      .. automethod:: __init__(name: str, description: str, component_list: List[MealComponent])

         :param name: The name of the meal.
         :type name: str
         :param description: A description of the meal.
         :type description: str
         :param component_list: A list of components that make up the meal.
         :type component_list: List[MealComponent]
         :raises ValueError: If name, description, or component_list are empty.

      .. automethod:: from_pydantic(pydantic_meal: PydanticMeal) -> "Meal"

         Factory method to create a business logic Meal object from a Pydantic Meal data model.

         :param pydantic_meal: The Pydantic meal object.
         :type pydantic_meal: PydanticMeal
         :return: A new Meal object.
         :rtype: Meal

      .. automethod:: to_pydantic() -> PydanticMeal

         Converts the business logic Meal object into its Pydantic representation for serialization.

         :return: A Pydantic Meal object.
         :rtype: PydanticMeal

      .. automethod:: as_dict() -> Dict[str, Any]

         Serializes the meal to a dictionary.

         :return: A dictionary representation of the meal.
         :rtype: Dict[str, Any]

      .. automethod:: add_component(component: MealComponent)

         Adds a new component to the meal.

         :param component: The meal component to add.
         :type component: MealComponent

      .. automethod:: remove_component(component_id: uuid.UUID) -> bool

         Removes a component from the meal by its ID.

         :param component_id: The ID of the component to remove.
         :type component_id: uuid.UUID
         :return: True if the component was removed, False otherwise.
         :rtype: bool

      .. automethod:: get_component_by_id(component_id: uuid.UUID) -> MealComponent | None

         Retrieves a meal component by its ID.

         :param component_id: The ID of the component to retrieve.
         :type component_id: uuid.UUID
         :return: The found MealComponent object, or None if not found.
         :rtype: MealComponent | None
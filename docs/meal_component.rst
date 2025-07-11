.. _meal_component-module:

**************
meal_component
**************

.. automodule:: meal_generator.meal_component
   :members:
   :undoc-members:
   :show-inheritance:

   .. autoclass:: MealComponent
      :members:
      :undoc-members:
      :show-inheritance:

      Represents a single component of a meal.

      .. automethod:: __init__(name: str, quantity: str, total_weight: float, nutrient_profile: NutrientProfile, brand: Optional[str] = None)

         :param name: The name of the component.
         :type name: str
         :param quantity: The quantity of the component (e.g., "1 cup").
         :type quantity: str
         :param total_weight: The total weight of the component in grams.
         :type total_weight: float
         :param nutrient_profile: The nutrient profile of the component.
         :type nutrient_profile: NutrientProfile
         :param brand: The brand of the component, if any.
         :type brand: str, optional

      .. automethod:: from_pydantic(pydantic_component: Component) -> "MealComponent"

         Factory method to create a MealComponent business object from its Pydantic data model representation.

         :param pydantic_component: The Pydantic component object.
         :type pydantic_component: Component
         :return: A new MealComponent object.
         :rtype: MealComponent

      .. automethod:: to_pydantic() -> Component

         Converts the MealComponent business object into its Pydantic data model representation for serialization.

         :return: A Pydantic Component object.
         :rtype: Component

      .. automethod:: as_dict() -> dict

         Serializes the meal component to a dictionary.

         :return: A dictionary representation of the meal component.
         :rtype: dict
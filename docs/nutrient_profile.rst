.. _nutrient_profile-module:

****************
nutrient_profile
****************

.. automodule:: meal_generator.nutrient_profile
   :members:
   :undoc-members:
   :show-inheritance:

   .. autoclass:: NutrientProfile
      :members:
      :undoc-members:
      :show-inheritance:

      Holds the nutrient information and dietary properties for a meal or meal component. This class is immutable.

      .. attribute:: energy
         :type: float

         Total energy in kilocalories (kcal).

      .. attribute:: fats
         :type: float

         Total fats in grams (g).

      .. attribute:: saturated_fats
         :type: float

         Saturated fats in grams (g).

      .. attribute:: carbohydrates
         :type: float

         Total carbohydrates in grams (g).

      .. attribute:: sugars
         :type: float

         Total sugars in grams (g).

      .. attribute:: fibre
         :type: float

         Total fibre in grams (g).

      .. attribute:: protein
         :type: float

         Total protein in grams (g).

      .. attribute:: salt
         :type: float

         Total salt in grams (g).

      .. attribute:: contains_dairy
         :type: bool

         True if the item contains dairy.

      .. attribute:: contains_high_dairy
         :type: bool

         True if the item contains a high amount of dairy.

      .. attribute:: contains_gluten
         :type: bool

         True if the item contains gluten.

      .. attribute:: contains_high_gluten
         :type: bool

         True if the item contains a high amount of gluten.

      .. attribute:: contains_histamines
         :type: bool

         True if the item contains histamines.

      .. attribute:: contains_high_histamines
         :type: bool

         True if the item contains a high amount of histamines.

      .. attribute:: contains_sulphites
         :type: bool

         True if the item contains sulphites.

      .. attribute:: contains_high_sulphites
         :type: bool

         True if the item contains a high amount of sulphites.

      .. attribute:: contains_salicylates
         :type: bool

         True if the item contains salicylates.

      .. attribute:: contains_high_salicylates
         :type: bool

         True if the item contains a high amount of salicylates.

      .. attribute:: contains_capsaicin
         :type: bool

         True if the item contains capsaicin.

      .. attribute:: contains_high_capsaicin
         :type: bool

         True if the item contains a high amount of capsaicin.

      .. attribute:: is_processed
         :type: bool

         True if the item is processed.

      .. attribute:: is_ultra_processed
         :type: bool

         True if the item is ultra-processed.

      .. automethod:: __init__(...)

         Initializes a NutrientProfile object. All parameters are optional and default to 0.0 for numeric fields and False for boolean fields.

      .. automethod:: from_pydantic(pydantic_profile: PydanticNutrientProfile) -> "NutrientProfile"

         Factory method to create a NutrientProfile business object from its Pydantic data model representation.

         :param pydantic_profile: The Pydantic nutrient profile object.
         :type pydantic_profile: PydanticNutrientProfile
         :return: A new NutrientProfile object.
         :rtype: NutrientProfile

      .. automethod:: to_pydantic() -> PydanticNutrientProfile

         Converts the NutrientProfile business object into its Pydantic data model representation for serialization.

         :return: A Pydantic NutrientProfile object.
         :rtype: PydanticNutrientProfile

      .. automethod:: as_dict() -> Dict[str, Any]

         Serializes the nutrient profile to a dictionary.

         :return: A dictionary representation of the nutrient profile.
         :rtype: Dict[str, Any]
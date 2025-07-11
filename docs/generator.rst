.. _generator-module:

*********
generator
*********

.. automodule:: meal_generator.generator
   :members:
   :undoc-members:
   :show-inheritance:

   .. autoclass:: MealGenerator
      :members:
      :undoc-members:
      :show-inheritance:

      .. automethod:: __init__(api_key: Optional[str] = None)

         Initializes the MealGenerator.

         :param api_key: The API key for accessing the Generative AI model. If not provided, it's expected to be set as an environment variable (e.g., GEMINI_API_KEY).
         :type api_key: str, optional

      .. automethod:: generate_meal(natural_language_string: str) -> Meal

         Takes a natural language string, sends it to the Generative AI model, and returns a structured Meal object.

         :param natural_language_string: A natural language description of the meal (e.g., "A classic cheeseburger with fries").
         :type natural_language_string: str
         :return: An object representing the generated meal with its components and aggregated nutrient profile.
         :rtype: Meal
         :raises ValueError: If the input natural language string is empty.
         :raises MealGenerationError: If there's any failure in the generation process, such as API communication issues, invalid JSON response, or malformed data.

   .. autoclass:: MealGenerationError
      :members:
      :undoc-members:
      :show-inheritance:

      Custom exception for errors during meal generation.
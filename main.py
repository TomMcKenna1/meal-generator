import asyncio
import logging
from src.meal_generator.generator import MealGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def run_generator():
    """
    Main async function to generate a meal and test adding a new component.
    """
    generator = MealGenerator()

    initial_query = "three alcoholic pints of guiness"
    print(f"--- 1. GENERATING INITIAL MEAL for query: '{initial_query}' ---\n")

    try:
        meal = await generator.generate_meal_async(initial_query)
        print("\n--- INITIAL MEAL CREATED ---\n")
        print(meal.as_dict())

        # add_component_query = "and a can of coke zero"
        # print(f"\n--- 2. ADDING NEW COMPONENT for query: '{add_component_query}' ---\n")

        # await meal.add_component_from_string_async(add_component_query, generator)

        # print("\n--- UPDATED MEAL WITH NEW COMPONENT ---\n")
        # print(meal.as_dict())

    except Exception as e:
        logging.error("An error occurred during the generation process.", exc_info=True)
        print(f"\n--- ERROR ---\nAn error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(run_generator())

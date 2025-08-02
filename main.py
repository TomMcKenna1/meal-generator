import asyncio
import logging
from src.meal_generator.generator import MealGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    async def run_generator():
        generator = MealGenerator()
        query = "Dominos thin and crispy mighty meaty pizza ad garlic and herb big dip"

        try:
            print(f"--- Running query: '{query}' ---")
            meal = await generator.generate_meal_async(query)
            print("\n--- FINAL MEAL OUTPUT ---")
            print(meal.as_dict())
        except Exception as e:
            print(f"An error occurred: {e}")

    asyncio.run(run_generator())

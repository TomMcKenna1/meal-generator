from src.meal_generator.generator import MealGenerator

if __name__ == "__main__":
    meal_generator = MealGenerator()

    meal_description = "large wrap with half a cup of rice, 100g of chilli, a tablespoon of soured cream"

    try:
        meal = meal_generator.generate_meal(meal_description)
        print("--- Meal Generated Successfully ---")
        print(meal)
        print("\n--- Meal as Dictionary ---")
        for component in meal.component_list:
            print(component.as_dict())
    except Exception as e:
        print(f"An error occurred: {e}")

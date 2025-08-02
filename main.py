from src.meal_generator.generator import MealGenerator

if __name__ == "__main__":
    meal_generator = MealGenerator(api_key="AIzaSyC7uRxfnoTgWA6KbI2mqHdZfxFMfA6RWe0")

    meal_description = "medium pepperoni pizza with a burrata from Zia Lucia"

    try:
        meal = meal_generator.generate_meal(meal_description)
        print("--- Meal Generated Successfully ---")
        print(meal)
        print("\n--- Meal as Dictionary ---")
        for component in meal.component_list:
            print(component.as_dict())
    except Exception as e:
        print(f"An error occurred: {e}")

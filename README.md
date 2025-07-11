# Meal Generator

[![PyPI version](https://badge.fury.io/py/meal-generator.svg)](https://badge.fury.io/py/meal-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package that uses a Generative AI model to parse natural language descriptions of meals and returns a detailed breakdown, including components, estimated weights, and a comprehensive nutrient profile.

***

## Features

-   **Natural Language Processing**: Understands descriptions of meals like "a bowl of oatmeal with a sliced banana and a drizzle of honey."
-   **Component Breakdown**: Identifies individual ingredients within the meal.
-   **Nutrient Analysis**: Provides estimated nutritional information for each component, including calories, macronutrients, and common allergens.
-   **Structured Output**: Returns data as organized Python objects for easy integration into your applications.

***

## Documentation
For a complete API reference and more detailed information, please visit the full documentation on [Read The Docs](https://meal-generator.readthedocs.io/en/latest).

***

## Installation

Install the package using pip:

```bash
pip install meal-generator
````

You will also need to have a Google Gemini API key. You can set this as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key"
```

-----

## Usage

Here is a quick example of how to use the `MealGenerator`:

```python
from meal_generator import MealGenerator, MealGenerationError

# Initialize the generator (it will use the GEMINI_API_KEY environment variable)
generator = MealGenerator()

meal_description = "A grilled chicken salad with lettuce, tomatoes, cucumbers, and a light vinaigrette dressing."

try:
    # Generate the meal object
    meal = generator.generate_meal(meal_description)

    # Print the meal's aggregated nutrient profile
    print(f"Meal: {meal.name}")
    print(f"Description: {meal.description}")
    print("\n--- Aggregated Nutrients ---")
    print(meal.nutrient_profile)

    # Print details for each component
    print("\n--- Meal Components ---")
    for component in meal.component_list:
        print(f"- {component.name} ({component.quantity}): {component.total_weight}g")
        print(f"  {component.nutrient_profile}")

except MealGenerationError as e:
    print(f"Error generating meal: {e}")
except ValueError as e:
    print(f"Input error: {e}")

```

### Example Input & Output

Here is an example of the data generated from a specific natural language query.

**Input String**:

```
"large wrap with half a cup of rice, 100g of chilli, a tablespoon of soured cream"
```

**Resulting `meal` Object Data**:

The code would produce a `meal` object containing the following structured data:

```json
{
  "meal": {
    "name": "Chilli Con Carne Wrap",
    "description": "A large wheat tortilla wrap filled with chilli con carne, white rice, and a tablespoon of soured cream.",
    "components": [
      {
        "name": "Large Wrap (Wheat Tortilla)",
        "brand": null,
        "quantity": "large wrap",
        "totalWeight": 70.0,
        "nutrientProfile": {
          "energy": 220.0,
          "fats": 5.0,
          "saturated_fats": 1.0,
          "carbohydrates": 38.0,
          "sugars": 1.0,
          "fibre": 2.0,
          "protein": 6.0,
          "salt": 0.8,
          "contains_dairy": false,
          "contains_high_dairy": false,
          "contains_gluten": true,
          "contains_high_gluten": true,
          "contains_histamines": false,
          "contains_high_histamines": false,
          "contains_sulphites": false,
          "contains_high_sulphites": false,
          "contains_salicylates": false,
          "contains_high_salicylates": false,
          "contains_capsaicin": false,
          "contains_high_capsaicin": false,
          "is_processed": true,
          "is_ultra_processed": true
        }
      },
      {
        "name": "Cooked White Rice",
        "brand": null,
        "quantity": "half a cup",
        "totalWeight": 95.0,
        "nutrientProfile": {
          "energy": 125.0,
          "fats": 0.3,
          "saturated_fats": 0.1,
          "carbohydrates": 28.0,
          "sugars": 0.0,
          "fibre": 0.3,
          "protein": 2.5,
          "salt": 0.0,
          "contains_dairy": false,
          "contains_high_dairy": false,
          "contains_gluten": false,
          "contains_high_gluten": false,
          "contains_histamines": false,
          "contains_high_histamines": false,
          "contains_sulphites": false,
          "contains_high_sulphites": false,
          "contains_salicylates": false,
          "contains_high_salicylates": false,
          "contains_capsaicin": false,
          "contains_high_capsaicin": false,
          "is_processed": false,
          "is_ultra_processed": false
        }
      },
      {
        "name": "Chilli (Con Carne/Stew)",
        "brand": null,
        "quantity": "100g",
        "totalWeight": 100.0,
        "nutrientProfile": {
          "energy": 130.0,
          "fats": 6.0,
          "saturated_fats": 2.5,
          "carbohydrates": 10.0,
          "sugars": 3.0,
          "fibre": 4.0,
          "protein": 12.0,
          "salt": 0.6,
          "contains_dairy": false,
          "contains_high_dairy": false,
          "contains_gluten": false,
          "contains_high_gluten": false,
          "contains_histamines": true,
          "contains_high_histamines": false,
          "contains_sulphites": false,
          "contains_high_sulphites": false,
          "contains_salicylates": true,
          "contains_high_salicylates": false,
          "contains_capsaicin": true,
          "contains_high_capsaicin": false,
          "is_processed": true,
          "is_ultra_processed": false
        }
      },
      {
        "name": "Soured Cream",
        "brand": null,
        "quantity": "a tablespoon",
        "totalWeight": 15.0,
        "nutrientProfile": {
          "energy": 35.0,
          "fats": 3.8,
          "saturated_fats": 2.2,
          "carbohydrates": 0.5,
          "sugars": 0.5,
          "fibre": 0.0,
          "protein": 0.5,
          "salt": 0.02,
          "contains_dairy": true,
          "contains_high_dairy": true,
          "contains_gluten": false,
          "contains_high_gluten": false,
          "contains_histamines": true,
          "contains_high_histamines": false,
          "contains_sulphites": false,
          "contains_high_sulphites": false,
          "contains_salicylates": false,
          "contains_high_salicylates": false,
          "contains_capsaicin": false,
          "contains_high_capsaicin": false,
          "is_processed": true,
          "is_ultra_processed": false
        }
      }
    ]
  }
}
```

-----

## Contributing

Contributions are welcome\! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/TomMcKenna1/meal-generator).

-----

## License

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
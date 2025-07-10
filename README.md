# Meal Generator

[![PyPI version](https://badge.fury.io/py/meal-generator.svg)](https://badge.fury.io/py/meal-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package that uses a Generative AI model to parse natural language descriptions of meals and returns a detailed breakdown, including components, estimated weights, and a comprehensive nutrient profile.

## Features

- **Natural Language Processing**: Understands descriptions of meals like "a bowl of oatmeal with a sliced banana and a drizzle of honey."
- **Component Breakdown**: Identifies individual ingredients within the meal.
- **Nutrient Analysis**: Provides estimated nutritional information for each component, including calories, macronutrients, and common allergens.
- **Structured Output**: Returns data as organized Python objects for easy integration into your applications.

## Installation

Install the package using pip:

```bash
pip install meal-generator
```

You will also need to have a Google Gemini API key. You can set this as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key"
```

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

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/TomMcKenna1/meal-generator).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
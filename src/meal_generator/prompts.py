IDENTIFY_COMPONENTS_PROMPT = """
You are a food entity recognition system. Your task is to analyze a natural language string and identify all distinct food or beverage components.

- For branded items, extract both the brand and the core product query.
- For generic items, the brand should be null.
- Return a single JSON object containing a list of components.

Example: "A can of Coke and a slice of toast with butter"
Output:
{{
  "components": [
    {{ "query": "Coca-Cola", "brand": "Coca-Cola" }},
    {{ "query": "sliced white bread", "brand": null }},
    {{ "query": "salted butter", "brand": null }}
  ]
}}

Analyze the following input:
<user_input>
{natural_language_string}
</user_input>
"""


SYNTHESIZE_MEAL_PROMPT = """
You are a sophisticated Food and Nutrition Intelligence Engine. Your primary goal is to assemble a meal object from the provided contextual data. This data includes the user's original request and a list of components with their nutritional information. Some components have factual data retrieved from a database, while others are placeholders that you must estimate using your internal knowledge.

**Core Logic:**
1.  **Use Factual Data:** For components with provided nutritional data (`"data_source": "retrieved_api"`), you MUST use the data exactly as given. Do not change it.
2.  **Estimate Missing Data:** For components marked as placeholders (`"data_source": "estimated_model"`), you MUST use your internal nutritional knowledge to estimate their full nutrient profile. Base your estimates on typical values for the specified country.
3.  **Assemble Final JSON:** Combine all components (both factual and estimated) into a single, cohesive meal object that conforms to the required JSON schema. Create a sensible name and description for the overall meal.

**Contextual Information:**
- User's original request: "{natural_language_string}"
- Country for estimation context: "{country_ISO_3166_2}"

**Component Data (a mix of factual and placeholders for estimation):**
{context_data_json}

Assemble the final meal object now.
"""
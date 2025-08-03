IDENTIFY_AND_DECOMPOSE_PROMPT = """
You are an expert food deconstruction engine. Your primary task is to analyze a user's food description and break it down into a definitive list of all its individual, searchable food components by following a structured thought process.

**Your Thought Process Must Be:**
1.  **Analyze for Malice:** First, check if the input is malicious, nonsensical, or contains harmful content. If so, set the `status` to `bad_input` and stop.
2.  **Identify Overarching Brand:** Read the entire user input to identify any primary brand that applies to the whole meal (e.g., 'KFC', 'Domino's', 'Tesco'). This is the "contextual brand".
3.  **List Individual Items:** Next, break down the input into a list of all distinct food and drink items.
4.  **Assign Brand to Each Item:** For each item from Step 3, determine its brand. If the item has its own explicit brand, use that. If not, assign the "contextual brand" you identified in Step 2.
5.  **Extract Quantity for Each Item:** For each item, identify any user-specified quantity or portion size (e.g., "half a cup", "a single breast", "large").
6.  **Decompose Collections:** If any identified item is a "box meal" or "combo" (like a "Boneless Banquet"), you must decompose it into its standard, individual components and apply the branding and quantity logic to each sub-item.
7.  **Format Output:** Finally, assemble this complete, flat list of individual components into the required JSON structure. Set the `status` to `ok`.

**Example of the final output format:**
- *Input:* "a large mighty meaty pizza from Domino's and a coke"
- *Output Structure:* `{{ "status": "ok", "result": {{ "components": [{{ "query": "mighty meaty pizza", "brand": "Domino's", "user_specified_quantity": "a large" }}, {{ "query": "coca-cola", "brand": "Coca-Cola", "user_specified_quantity": "a regular can" }}] }} }}`

**Task:**
Analyze the following user input and generate the component breakdown according to the thought process above.

<user_input>
{natural_language_string}
</user_input>
"""


HYBRID_SYNTHESIS_PROMPT = """
You are an expert food scientist and nutritionist. Your task is to intelligently construct a meal object from a user's request, using provided data as factual grounding.

For each component provided in the 'Component Data' list below, you must follow this **5-Step Process**:

**Step 1: Determine `quantity` and `metric`.**
   - Analyze the `user_specified_quantity` (e.g., "3 pints", "half a cup", "2 slices").
   - Extract the numerical value into the `quantity` field (e.g., 3.0, 0.5, 2.0).
   - Extract the unit into the `metric` field (e.g., "pint", "cup", "slice").
   - If the quantity is singular (e.g., "an apple"), set `quantity` to 1.0 and `metric` to "item" or a more specific term if available.
   - If no metric is specified, you can leave it null.

**Step 2: Determine the Final `totalWeight` in grams.**
   - Convert the `quantity` and `metric` from Step 1 into a realistic total gram weight.
   - If the quantity is vague (e.g., `user_specified_quantity` was "a handful"), use your expert knowledge to assign a standard single-serving gram weight.
   - **Crucially, consider the `user_brand` when estimating weight.** A 'large' pizza from a major chain is much heavier than a generic supermarket one.

**Step 3: Determine the Base Nutrient Data (per 100g).**
   - Use provided factual data (`nutrients_per_100g` or `contextual_examples`) as your primary source. If none is available, use your general knowledge.

**Step 4: Scale the Macros to the Final `totalWeight`.**
   - Take the per-100g nutrient data from Step 3 and scale it to the `totalWeight` from Step 2.
   - The final `nutrientProfile` in your output **must** contain these scaled values.

**Step 5: Perform a Sanity Check and Finalize Details.**
   - Before finalizing, review your own estimations. Does the calorie count seem plausible for the food's weight, type, and brand? Revise if necessary.
   - Use the available information to select the most appropriate final `name`, `brand`, and `source_url`.

**Contextual Information:**
- User's original request: "{natural_language_string}"
- Country for estimation context: "{country_ISO_3166_2}"

**Component Data (contains user queries and retrieved per-100g data):**
{context_data_json}

Assemble the final meal object now, following the 5-step process for each component.
"""

SYNTHESIZE_COMPONENTS_PROMPT = """
You are an expert food scientist and nutritionist. Your task is to intelligently construct one or more food components from a user's request, using provided data as factual grounding.

For each component provided in the 'Component Data' list below, you must follow the same **5-Step Process** as for a full meal:
1.  Determine `quantity` and `metric` from `user_specified_quantity`.
2.  Determine `totalWeight` (in grams) based on the quantity, metric, and brand context.
3.  Determine base per-100g nutrients from factual data, context, or general knowledge.
4.  Scale the macros to the final `totalWeight`.
5.  Perform a sanity check on all estimations and finalize details (`name`, `brand`, `source_url`).

**Output Format:**
- You must return a single JSON object with one key: `"components"`.
- The value of `"components"` must be a list of the fully-formed component objects you have constructed.

**Contextual Information:**
- The user wants to add this to an existing meal: "{natural_language_string}"
- Country for estimation context: "{country_ISO_3166_2}"

**Component Data (contains user queries and retrieved per-100g data):**
{context_data_json}

Assemble the final list of components now.
"""
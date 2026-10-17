
import streamlit as st
import requests

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="ChefAI - Personal Kitchen Assistant",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Custom Styling
# --------------------------------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton > button {
        width: 100%;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.6rem;
        border: none;
    }
    .stButton > button:hover {
        background-color: #e03e3e;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# OpenRouter Configuration
# --------------------------------------------------
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free-model router. You can replace this with a
# specific free model ID from OpenRouter's catalogue.
MODEL_NAME = "openrouter/free"


def generate_recipes(ingredients, dietary, meal_type, temperature):
    """Send the recipe request to OpenRouter."""

    # Read the API key from Streamlit secrets.
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")

    if not api_key:
        raise ValueError(
            "OpenRouter API key is missing. "
            "Configure OPENROUTER_API_KEY in Streamlit secrets."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "ChefAI - Personal Kitchen Assistant",
    }

    prompt = f"""
You are ChefAI, an expert professional chef and
culinary assistant.

Available ingredients: {ingredients}
Dietary preference or restriction: {dietary}
Target meal type: {meal_type}

Rules:
- Suggest 1 creative, appetizing recipes.
- Use the user's available ingredients as the main ingredients.
- You may assume salt, pepper, water, cooking oil,
  and basic flour or sugar are available.
- Respect the selected dietary preference.
- If the selected preference is None, do not impose
  a special dietary restriction.
- Match the selected meal type.
- Do not claim a recipe is gluten-free, vegan, or
  suitable for another restriction if its ingredients
  do not meet that requirement.
- If ingredients conflict with the dietary restriction,
  explain the conflict and suggest safe substitutions.

For each recipe include:
1. Recipe name
2. Preparation time and cooking time
3. Ingredients, marking those supplied by the user
4. Clear, numbered cooking instructions

Use clean Markdown and helpful food emojis.
Keep the answer practical and easy to follow.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are ChefAI, a helpful cooking assistant. "
                    "Give clear, practical recipe suggestions."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": 1200
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=90
    )

    # Convert HTTP errors into readable error messages.
    if not response.ok:
        try:
            details = response.json().get("error", {})
            message = details.get("message", response.text)
        except (ValueError, AttributeError):
            message = response.text

        raise RuntimeError(
            f"OpenRouter returned HTTP {response.status_code}: "
            f"{message}"
        )

    data = response.json()

    # Check that the model returned usable text.
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(
            "The AI model returned no response. Please try again."
        )

    content = choices[0].get("message", {}).get("content", "")

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
        )

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "The AI returned an empty recipe. Please try again."
        )

    return content


# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("⚙️ AI Settings")

    st.caption("Powered by OpenRouter cloud AI")

    temperature = st.slider(
        "Creativity (Temperature)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1
    )

    st.markdown("---")
    st.markdown("### 📌 Quick Tips")
    st.markdown(
        "1. Enter ingredients separated by commas.\n"
        "2. Select your dietary preference.\n"
        "3. Choose your preferred meal type.\n"
        "4. Click Generate Recipes."
    )
    st.caption(
        "AI availability depends on the selected model "
        "and its usage limits."
    )


# --------------------------------------------------
# Main Page
# --------------------------------------------------
st.title("🍳 ChefAI: Smart Kitchen Assistant")

st.markdown(
    "Turn your leftover ingredients into delicious "
    "meals using AI."
)

col1, col2 = st.columns([2, 1])

with col1:
    ingredients = st.text_area(
        "🛒 Available Ingredients:",
        placeholder=(
            "e.g., chicken breast, garlic, olive oil, "
            "lemon, spinach, rice"
        ),
        height=120
    )

with col2:
    dietary = st.selectbox(
        "🥗 Dietary Preference",
        [
            "None",
            "Vegetarian",
            "Vegan",
            "Gluten-Free",
            "Keto",
            "Low-Carb",
            "Dairy-Free"
        ]
    )

    meal_type = st.selectbox(
        "🕒 Meal Type",
        [
            "Any",
            "Breakfast",
            "Lunch",
            "Dinner",
            "Snack",
            "Quick Bite"
        ]
    )


# --------------------------------------------------
# Generate Recipes
# --------------------------------------------------
if st.button("✨ Generate Recipes"):
    if not ingredients.strip():
        st.warning(
            "⚠️ Please enter at least a few ingredients!"
        )

    else:
        try:
            with st.spinner(
                "👨‍🍳 ChefAI is preparing your recipes..."
            ):
                result = generate_recipes(
                    ingredients=ingredients.strip(),
                    dietary=dietary,
                    meal_type=meal_type,
                    temperature=temperature
                )

            st.markdown("---")
            st.subheader("🍽️ Recommended Recipes for You")
            st.markdown(result)

        except Exception as e:
            st.error(f"❌ Could not generate recipes: {e}")
            st.info(
                "Check your API key, model availability, "
                "internet connection, and usage limits."
            )

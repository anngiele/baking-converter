import streamlit as st
from fractions import Fraction
import pandas as pd
import logging
import os
import json
from datetime import datetime

#log setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/app.log'),
    ]
)

logger = logging.getLogger(__name__)

#conversion log
conversions_log = "conversion_history.json"

def load_conversion_history():
    "Load Conversion History from JSON"
    if os.path.exists(conversions_log):
        try:
            with open(conversions_log, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_conversion_history(history):
    "Save conversion history to JSON"
    with open(conversions_log, 'w') as f:
        json.dump(history, f, indent = 4)

def log_conversion(ingredient, cups, grams):
    "Add a conversion to the history"
    history = load_conversion_history()

    conversion_entry = {
        "timestamp": datetime.now().isoformat(),
        "ingredient": ingredient,
        "cups": round(cups,2),
        "grams": round(grams,2),
    }

    history.append(conversion_entry)
    save_conversion_history(history)
    logger.info(f"Logged conversion: {cups} cups of {ingredient} = {grams:.1f}g")

st.set_page_config(page_title="Baking Converter", layout="wide")
st.title("Baking Converter for Accurate Measurements! :)")

#conversions 1 cup to grams
conversion = {
    "flour": 120,
    "sugar": 200,
    "butter": 227,
    "brown sugar": 220,
    "milk": 240,
    "cocoa powder": 85,
    "salt": 6,
    "baking powder": 5,
    "vanilla extract": 5
}

#functions
def parse_amount(amount_str):
    try:
        parts = amount_str.split()
        if len(parts) == 2:
            whole = float(parts[0])
            frac = float(Fraction(parts[1]))
            return whole + frac
        else:
            return float(Fraction(amount_str))
    except:
        return None

def scale_recipe(recipe_dict, scale_factor):
    """Scale all recipe amounts by a factor"""
    return {ing: amount * scale_factor for ing, amount in recipe_dict.items()}

#tabs
tab1, tab2 = st.tabs(["Converter","History"])

#converter
with tab1:
    st.subheader("Converter Settings")
    mode = st.radio("Converter Type:", ["Single Ingredient", "Recipe Scaler", "Multiple Ingredient Converter"])
    
    show_reference = st.checkbox("Show reference table", value=True)

#single
if mode == "Single Ingredient":
    st.subheader("Convert Single Ingredient")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ingredient = st.selectbox("Select ingredient:", list(conversion.keys()))
    
    with col2:
        amount_input = st.text_input(
            "Enter amount in cups:",
            placeholder="e.g., 1, 1/2, 1 1/2"
        )
    
    if st.button("Convert", type="primary"):
        if amount_input:
            cups = parse_amount(amount_input)
            if cups is not None:
                grams = cups * conversion[ingredient]
                
                log_conversion(ingredient, cups, grams)

                #display result
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Cups", f"{cups}")
                with col2:
                    st.metric("Grams", f"{grams:.1f}")
                
                st.success(f"{cups} cup(s) of **{ingredient}** = **{grams:.1f}g**")
            else:
                st.error("Invalid amount format")
        else:
            st.error("Please enter an amount")

#recipe
elif mode == "Recipe Scaler":
    st.subheader("Recipe Scaler")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Original Recipe**")
        recipe = {}
        ingredients_to_add = st.multiselect(
            "Select ingredients:",
            list(conversion.keys()),
            default=["flour", "sugar", "butter"]
        )
        
        for ing in ingredients_to_add:
            amount = st.number_input(
                f"{ing.title()} (cups):",
                min_value=0.0,
                step=0.25,
                value=1.0,
                key=f"orig_{ing}"
            )
            recipe[ing] = amount
    
    with col2:
        st.write("**Scale Factor**")
        scale_factor = st.slider(
            "Multiply recipe by:",
            min_value=0.25,
            max_value=4.0,
            step=0.25,
            value=1.0
        )
    
    if recipe:
        scaled_recipe = scale_recipe(recipe, scale_factor)
        
        st.subheader("Scaled Recipe")
        
        #dataframes
        df_data = {
            "Ingredient": [ing.title() for ing in scaled_recipe.keys()],
            "Cups": [f"{amount:.2f}" for amount in scaled_recipe.values()],
            "Grams": [f"{amount * conversion[ing]:.1f}" for ing, amount in scaled_recipe.items()]
        }
        df = pd.DataFrame(df_data)
        st.dataframe(df, width="stretch")
        
        #download as csv
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="recipe.csv",
            mime="text/csv"
        )

#multiple ingredient
elif mode == "Multiple Ingredient Converter":
    st.subheader("Convert Multiple Ingredients")
    
    num_ingredients = st.slider("How many ingredients?", 1, 10, 3)
    
    conversions = {}
    for i in range(num_ingredients):
        col1, col2 = st.columns(2)
        
        with col1:
            ing = st.selectbox(
                f"Ingredient {i+1}:",
                list(conversion.keys()),
                key=f"batch_ing_{i}"
            )
        
        with col2:
            amount = st.text_input(
                f"Amount (cups):",
                placeholder="1, 1/2, 1 1/2",
                key=f"batch_amt_{i}"
            )
        
        if amount:
            parsed = parse_amount(amount)
            if parsed:
                conversions[ing] = parsed
    
    if st.button("Convert All", type="primary"):
        if conversions:
            results = []
            for ing, cups in conversions.items():
                grams = cups * conversion[ing]
                results.append({
                    "Ingredient": ing.title(),
                    "Cups": f"{cups:.2f}",
                    "Grams": f"{grams:.1f}"
                })
            
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, width="stretch")

#ref table
if show_reference:
    with st.expander("Conversion Reference", expanded=False):
        df_ref = pd.DataFrame({
            "Ingredient": [ing.title() for ing in conversion.keys()],
            "Grams per Cup": list(conversion.values())
        })
        st.dataframe(df_ref, width="stretch")


with tab2:
    st.subheader("Conversion History of Single Ingredients")
    
    history = load_conversion_history()
    
    if history:
        
        df_history = pd.DataFrame(history)
        
       
        df_display = df_history[["timestamp", "ingredient", "cups", "grams"]].copy()
        df_display.columns = ["Time", "Ingredient", "Cups", "Grams"]
        
        #time
        df_display["Time"] = pd.to_datetime(df_display["Time"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # most recent on top
        st.dataframe(df_display.iloc[::-1], width="stretch", hide_index=True)
        
    
        st.divider()
        st.subheader("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"conversion_history.csv",
                mime="text/csv",
                width = "stretch"
            )
        
        with col2:
            json_data = json.dumps(history, indent=2)
            st.download_button(
                label="Download as JSON",
                data=json_data,
                file_name=f"conversion_history.json",
                mime="application/json",
                width="stretch"
            )
        
        with col3:
            if st.button("Clear History", width="stretch", type="secondary"):
                save_conversion_history([])
                logger.warning("Conversion history cleared")
                st.rerun()
    else:
        st.info("No conversion history yet. Make some conversions to get started!")

#bottom footer
st.divider()
st.caption("Thank you! Happy Baking <3")
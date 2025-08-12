# Import python packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(f":cup_with_straw: Example Streamlit App :cup_with_straw:")
st.write("""
Choose the fruits you want in your custom Smoothie!
""")

name_on_order = st.text_input("Name on Smoothie", "")
st.write("The Name on your Smoothie will be:", name_on_order)

session = get_active_session()

# Pull both columns you need
sp_df = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = sp_df.to_pandas()

# Multiselect should receive a list of strings (fruit names)
options = sorted(pd_df['FRUIT_NAME'].tolist())

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    options,
    max_selections=5
)

# quick lookup map: fruit name -> search_on
search_map = dict(zip(pd_df['FRUIT_NAME'], pd_df['SEARCH_ON']))

# warning for multiselect (Streamlit already caps, but keeping your message)
if len(ingredients_list) > 5:
    st.warning('You have reached maximum smoothie capacity. Select only 5 ingredients')

if ingredients_list:
    # Show each fruit and its search term
    for fruit_chosen in ingredients_list:
        # search_on = search_map.get(fruit_chosen, fruit_chosen)  # fallback to name if missing
        # st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')
        ingredients_list += fruit_chosen + ' '

        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get('https://my.smoothiefroot.com/api/fruit/' + search_on)
        fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)

    # Build insert safely (escape single quotes)
    ingredients_string = ', '.join(ingredients_list)
    safe_ingredients = ingredients_string.replace("'", "''")
    safe_name = name_on_order.replace("'", "''")

    my_insert_stmt = f"""
    INSERT INTO smoothies.public.orders (ingredients, name_on_order)
    VALUES ('{safe_ingredients}', '{safe_name}')
    """

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")

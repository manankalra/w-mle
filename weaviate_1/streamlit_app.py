import streamlit as st
from streamlit_option_menu import option_menu

from ui import generate
from utils.client import access_client
from utils.query import query_arxiv

st.set_page_config(
    page_title="arXiv meets Weaviate - Manan Kalra",
    page_icon="img/weaviate.png",
    layout="wide",
    initial_sidebar_state="expanded",
)




ui = {
    # "README": (readme, "house-fill"),
    "Generate": (generate, "search"),
}



main_page = st.container()

navigation = st.sidebar.container()

with navigation:
    selected_page = option_menu(
        menu_title=None,
        options=list(ui.keys()),
        icons=[icon[1] for icon in ui.values()],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"border": "2px solid #847242"},
            "icon": {"font-size": "18px"},
            "nav-link": {"font-size": "20px", "text-align": "left"},
        },
    )

client = access_client()
ui[selected_page][0].show(client, main_page)
client.close()


# st.image('img/arxiv.png')
# st.text("meets")
# st.image('img/weaviate.png')
#
# st.title('ARXIV')

# client = access_client()

# with st.form('ARXIV_FORM'):
#     collection_name = st.text_area('Name of an already existing collections in WCS.')
#     query = st.text_area('Query')
#     # query_properties = st.text_area("Query Properties")
#     prompt = st.text_area('Prompt')
#     limit = st.text_area('Limit')
#
#     submitted = st.form_submit_button('Submit')
#
#     if submitted:
#         st.info(query_arxiv(client, collection_name, query, prompt, limit))
#
#     client.close()

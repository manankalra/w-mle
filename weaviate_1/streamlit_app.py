import streamlit as st

from ui import generate
from utils.client import access_client

st.set_page_config(
    page_title="arXiv meets Weaviate - Manan Kalra",
    page_icon="img/weaviate.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui = {"Generate": (generate, "search")}

main_page = st.container()
navigation = st.sidebar.container()

with navigation:
    with st.expander("About Arxiv meets Weaviate:"):
        st.markdown((
            """
            This app allows you to ask questions based on retrieved content from an embedded index of more than half 
            a million Arxiv papers. 

            Particularly, you'll be able to:
            - Provide a search keyword to shortlist the papers based on semantic search.
            - Ask any kind of questions based on the retrieved content.
            - Generate a response.
            """
        ))

    with st.expander("How it's built:"):
        st.markdown((
            """
            - The queries are performed on top of ingested vector embeddings in Weaviate Cloud.
            - The index is multi-tenant and also uses quantized vector spaces for improving scalability and latency,
            respectively.
            - HNSW-based index is built along with named vectors were used for certain fields.
            - Cohere's multi-lingual embedding model is used for populating the index with embeddgins whereas Claude's
            Sonnet serves as the generative model for thi task.  
            """
        ))

    with st.expander("Portfolio:"):
        st.markdown(("""
        - [LinkedIn](https://ie.linkedin.com/in/manankalra)
        - My portfolio / Product work:
            - [AI Copilots](https://www.genesys.com/en-gb/capabilities/agent-copilot)
            - [RAG](https://www.genesys.com/capabilities/knowledge-management)
            - [Bots](https://www.genesys.com/capabilities/voicebots)
            - [Predictive Routing](https://www.genesys.com/capabilities/automated-routing)
            - [Personalization/Recommendation Systems](https://www.genesys.com/capabilities/predictive-web-engagement)
        - [Weaviate](https://github.com/manankalra/w-mle)
        """))

client = access_client()
generate.show(client, main_page)
client.close()

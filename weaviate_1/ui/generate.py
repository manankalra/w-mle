import pandas as pd
import streamlit as st

from utils.query import query_arxiv


def show(client, container):
    with container:
        arxiv, weaviate = st.columns([5, 5])
        arxiv.image('img/arxiv.png')
        weaviate.image('img/weaviate.svg')

        collections = ["Arxiv", "JobPostings"]
        queries = ["Machine Learning/AI", "Astrophysics", "Healthcare/Cardiology"]
        prompts = [
            "",
            "Tell me something cool about the research content above but explain it to me in layman terms. "
            "Also point out the authors who are responsible for that research."
        ]

        collection = st.selectbox("Select an already populated collection:", collections, index=0)

        query = st.selectbox("Select keywords/queries:", queries, index=0)
        query = st.text_input(
            "",
            query,
            placeholder="Write a custom query.",
        )

        prompt = st.selectbox("(Optional) Select a prompt:", prompts, index=0)
        prompt = st.text_input(
            "",
            prompt,
            placeholder="Write a custom prompt.",
        )

        limit = st.slider('Select a response limit', 10, 100, 5)

        if "results" not in st.session_state:
            st.session_state.results = None

        if st.button("Run"):
            if not prompt:
                query_response = query_arxiv(
                    client=client,
                    collection_name=collection,
                    query=query,
                    limit=limit
                )
                # st.info(query_response.objects)
                res_display = []
                for res in query_response.objects:
                    res_display.append([res.properties["title"], res.properties["authors"], res.properties["categories"]])
                st.dataframe(pd.DataFrame(res_display, columns=["title", "authors", "categories"]))
                st.session_state.results = {"query_response": query_response.objects}
            elif prompt and query:
                generated_response = query_arxiv(
                    client=client,
                    collection_name=collection,
                    query=query,
                    prompt=prompt,
                    limit=limit
                )
                st.info(generated_response.generated)
                st.session_state.results = {"generated_response": generated_response.generated}
            else:
                st.error("Please enter a query.")
                st.session_state.results = None

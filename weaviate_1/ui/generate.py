import streamlit as st

from utils.query import query_arxiv


def show(client, container):
    with container:
        col1, col2, col3 = st.columns([3, 1, 3])
        col1.image('img/arxiv.png')
        col2.text("meets")
        col3.image('img/weaviate.png')
        st.title("Generate")
        st.write(
            "Query"
        )

        collections = ["JobPostings", "Arxiv"]
        queries = ["Machine Learning/AI", "Healthcare/Medicine", "Dietitian/Nutritionist"]
        prompts = [
            "Tell me something cool about the content above but explain it to me in layman terms. Also point out the "
            "authors who are responsible for that research."
        ]

        collection = st.selectbox("Select an already populated collection:", collections, index=0)

        query = st.selectbox("Select keywords/queries:", queries, index=0)
        query = st.text_input(
            "",
            query,
            placeholder="Write a custom query.",
        )

        prompt = st.selectbox("Select a prompt:", prompts, index=0)
        prompt = st.text_input(
            "",
            prompt,
            placeholder="Write a custom prompt.",
        )

        limit = st.slider('Select a response limit', min_value=10, max_value=50)

        if "results" not in st.session_state:
            st.session_state.results = None

        if st.button("Generate"):
            if query:
                generated_response = query_arxiv(client, collection, query, prompt, limit)
                st.info(generated_response)
                st.session_state.results = {"generated_response": generated_response}
            else:
                st.error("Please enter a query.")
                st.session_state.results = None

        if st.session_state.results:
            st.subheader("Generated response")
            st.write(st.session_state.results["generated_response"])

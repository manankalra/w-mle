def query_arxiv(client, collection_name: str, query: str, query_properties: list=None, prompt: str = None, limit: int = 50) -> str:
    """
    Performs either hybrid or generative search based on user request.

    Parameters
    ----------
    client :
        Client object
    collection_name : str
        Name of the collection

    query : str
        User query keywords

    query_properties : list
        Query properties

    prompt : str
        Additional question that the user can ask on top of the search responses.

    limit : int
        Number of search responses to return.

    Returns
    -------
    str
        Either the search results or the generated response by the LLM.

    """
    collection = client.collections.get(collection_name)

    # if the user included a prompt in the request, do a generative search
    # to answer the question based on the search response
    if prompt:
        response = collection.generate.hybrid(
            query=query,
            query_properties=["title", "abstract", "authors", "categories", "update_date"],
            # fields to use for keyword search
            grouped_task=str(prompt) + " Only answer this based on the data provided above.",
            # generation is performed on the search responses as a group, not on individual items in the response.
            # grouped_properties=["title"],
            limit=limit,
            alpha=0.75,  # want to favour the vector search more here
        )
    else:
        response = collection.query.hybrid(
            query=query,
            query_properties=query_properties,
            limit=limit,
            alpha=0.75,
        )

    return response

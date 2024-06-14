from weaviate.classes.config import Configure, VectorDistances

from .client import access_client
from .constants import (
    AWS_REGION,
    BEDROCK_SERVICE,
    CLAUDE_SONNET_BEDROCK_MODEL_ID,
    COHERE_EMBEDDING_MODEL_ID
)


def get_collection(client, collection_name, overwrite=False):
    if overwrite:
        # deleting the existing collection if it exists already, to create a new one later
        if client.collections.exists(collection_name):
            client.collections.delete(collection_name)

        client.collections.create(
            collection_name,
            vectorizer_config=Configure.Vectorizer.text2vec_aws(
                region=AWS_REGION,
                service=BEDROCK_SERVICE,
                model=COHERE_EMBEDDING_MODEL_ID,
            ),
            # multi_tenancy_config=Configure.multi_tenancy(
            #     enabled=True,
            #     auto_tenant_creation=True,
            #     auto_tenant_activation=True,
            # ),
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=VectorDistances.COSINE
            ),
            generative_config=Configure.Generative.aws(
                region=AWS_REGION,
                model=CLAUDE_SONNET_BEDROCK_MODEL_ID
            )
        )

    collection = client.collections.get(collection_name)

    return collection


def ingest_collection(client, collection_name, df_arr):
    collection = client.collections.get(collection_name)

    with collection.batch.dynamic() as batch:
        for entry in df_arr:
            batch.add_object(properties=entry)
import weaviate
from weaviate.auth import AuthApiKey
from weaviate.config import AdditionalConfig, Timeout

from .env import (
    WCS_URL,
    WEAVIATE_API_KEY,
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
    AWS_SESSION_TOKEN
)


def access_client():
    client = weaviate.connect_to_wcs(
        cluster_url=WCS_URL,
        auth_credentials=AuthApiKey(WEAVIATE_API_KEY),
        headers={
            "X-AWS-Access-Key": AWS_ACCESS_KEY,
            "X-AWS-Secret-Key": AWS_SECRET_KEY,
            "X-AWS-Session-Token": AWS_SESSION_TOKEN
        },
        additional_config=AdditionalConfig(
            timeout=Timeout(init=2, query=120, insert=120)
        )
    )
    # client = weaviate.connect_to_local()
    return client

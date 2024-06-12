# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC `Manan Kalra` - `Machine Learning Engineer, Genesys`
# MAGIC
# MAGIC `manankalra29@gmail.com` - `https://linkedin.com/in/manankalra`
# MAGIC
# MAGIC - <h4>Dataset</h4>
# MAGIC https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
# MAGIC   
# MAGIC - <h4>Description</h4>
# MAGIC The following pipeline allows you to ask exploratory questions related to thousands of job postings that were advertised on LinkedIn in the past two years and returns a succinct response in relation to the same.
# MAGIC
# MAGIC - <h4>How it works?</h4>
# MAGIC
# MAGIC   - After preprocessing the data, this workflow uses **Weaviate** to create vector embeddings for the job postings.
# MAGIC
# MAGIC     - Embeddings are stored in **Weaviate Cloud** for quick access at any time.
# MAGIC     - **Cohere**'s multilingual model is used to create embeddings. For generative tasks, Anthropic's Claude-**Sonnet** is used. 
# MAGIC     - Both are being accessed via **Bedrock**.
# MAGIC     - A collection named **JobPostings** was populated with the embeddings. The vector indices are created using **HNSW**.
# MAGIC     - Utility functiona are included to perform **hybrid search** either with a single query or **generative search** along with a prompt.
# MAGIC
# MAGIC   - It allows the user to answer questions like:
# MAGIC
# MAGIC     - **Which location has the most AI/ML jobs?**
# MAGIC     
# MAGIC       Example response: 
# MAGIC       
# MAGIC       Based on the data provided, the location that has the most AI/ML job postings is the United States. Several job postings list the location as "United States" or specific cities/regions within the United States such as New York City Metropolitan Area, Sunnyvale CA, Greater Chicago Area, Waltham MA, Bentonville AR, San Jose CA, and Los Angeles CA.
# MAGIC
# MAGIC     - **What is the average salary for the above included jobs? Also, which is the most frequent title for jobs in this domain?**
# MAGIC       
# MAGIC       Example response: 
# MAGIC       
# MAGIC       Based on the data provided, here are the answers to your questions:
# MAGIC       
# MAGIC       1. The average salary range for the included jobs is difficult to calculate precisely since many of the salary listings are incomplete or show wide ranges. However, based on the available data, a rough estimate of the average salary range would be around $200,000 - $300,000 per year.
# MAGIC
# MAGIC       2. The most frequent job title in this domain, based on the data provided, is "Family Practice-Without OB Physician". This title appears 9 times across the different job listings.
# MAGIC
# MAGIC       Please note that these answers are based solely on the data you provided, and may not represent the complete picture of salaries and job titles in this domain.
# MAGIC
# MAGIC     - **Are there any healthcare jobs in California? If yes, which city are they based in? Are any of them based in Irvine?**
# MAGIC
# MAGIC       Example response:
# MAGIC       
# MAGIC       Based on the data provided, there are several healthcare jobs located in California, specifically:
# MAGIC
# MAGIC       1. Telemedicine Physician - CA 100% Remote (Irvine, CA)
# MAGIC       2. Internal Medicine Physician - $125/hourly - $135/hourly (San Mateo, CA)
# MAGIC       3. Family Practice-Without OB Physician - $125/hourly - $135/hourly (San Mateo, CA)
# MAGIC       4. Family Practice-Without OB Physician - $133/yearly (Sacramento, CA)
# MAGIC       5. Family Practice-Without OB Physician - $275,000/yearly - $325,000/yearly (San Jose, CA)
# MAGIC       6. Medical Doctor (Silicon Valley, CA)
# MAGIC
# MAGIC       So yes, there are healthcare jobs listed in the data that are based in Irvine, California specifically for the role of "Telemedicine Physician - CA 100% Remote".
# MAGIC
# MAGIC - <h4>Limitations</h4>
# MAGIC   
# MAGIC   - Doesn't use any quantization techniques which could have been useful to compress the high-dimenstional embeddings.
# MAGIC   - Options to improve embeddgins aweren't explored. No named vectors were used as well.
# MAGIC   - HNSW uses the default params.
# MAGIC   - No multi-tenancy options are enabled for scalability.
# MAGIC

# COMMAND ----------

!pip3 install weaviate-client

# COMMAND ----------

# imports

import os
import json
import pandas as pd

import weaviate
from weaviate.auth import AuthApiKey
from weaviate.config import AdditionalConfig, Timeout
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Metrics

from pyspark.sql.types import ArrayType, FloatType
from pyspark.sql.functions import col, concat_ws, count, date_format, from_unixtime, isnan, isnull, round, udf, when

# COMMAND ----------

# load data

# using databricks here, if you need to re-run in Colab - please use a Google Drive mount instead for quick ingestion
postings_csv = "/dbfs/FileStore/tables/manan_dfs/wml/postings.csv"

# directly reading with spark gave me schema issues, this is juts a quick hack instead of creating the expected schema 
postings = spark.createDataFrame(pd.read_csv(postings_csv))

display(postings)

# COMMAND ----------

# looking here for potential missing values in job titles, descriptions, etc. to replace them with empty strings

# this is only to get some insights

# for example: >75% of the rows are missing salary related information
# so generative queries like  "What is the verage salary for a Machine Learning Engineer in Ney York?"" on a response set might not work well
# however, I've encountered some hallucinations

postings_rows = postings.count()

postings_missing = postings.select([
    round((count(when(isnull(c), c)) / postings_rows * 100), 2).alias(c) for c in postings.columns
])

postings_missing = postings_missing.toPandas().transpose().reset_index()
postings_missing.columns = ["feature", "missing_pct"]
postings_missing = spark.createDataFrame(postings_missing)

display(postings_missing)

# COMMAND ----------

# filling missing values

fill_values = {
    "company_name": " ",
    "description": " ",
    "description": " ",
    "formatted_experience_level": " ",
    "max_salary": " ",
    "min_salary": " ",
    "pay_period": " "
}

postings_filled = postings.fillna(fill_values)

# COMMAND ----------

# formatting date, might be helpful for embeddings

postings_filled = postings_filled.withColumn("formatted_date", from_unixtime(col("original_listed_time") / 1000).cast("timestamp"))
postings_filled = postings_filled.withColumn("formatted_date", date_format(col("formatted_date"), "MMMM d, y - EEEE"))

display(postings_filled.groupBy("formatted_date").count())

# COMMAND ----------

# using sentence-transformers, was trying to create my own vectors for a single column created by joining all features
# but later came across the built-in way to do it with Weaviate

# postings_filled = postings_filled.withColumn(
#   "posting_to_embed", 
#   concat_ws(
#     " ", 
#     col("title"),
#     col("company_name"),
#     col("description"),
#     col("location"),
#     col("formatted_experience_level"),
#     col("max_salary"),
#     col("min_salary"), 
#     col("pay_period"), 
#     col("formatted_work_type"),
#     col("formatted_date"),
#     col("job_posting_url"),
#   )
# )

# display(postings_filled.select("posting_to_embed"))

# COMMAND ----------

# converting to json for ingesting objects in batches
# there might be a way to do it with the dataframe too, haven't searched more in detail as I was familiar with this one already

postings_json = postings_filled.select(
  "title",
  "company_name",
  "description",
  "location",
  "formatted_experience_level",
  "max_salary",
  "min_salary",
  "pay_period",
  "formatted_work_type",
  "formatted_date",
  "job_posting_url",
).toJSON().collect()

postings_json = [json.loads(job_posting) for job_posting in postings_json]

# COMMAND ----------

# using weaviate cloud here, using the 14 day free-trial for now though
# prevents me creating a local backup or in S3

WCS_URL = "<use-your-own>"
WEAVIATE_API_KEY = "<use-your-own>"

# resorted to using Bedrock, as I've reached spending limits here
# OPENAI_API_KEY = "<use-your-own>"
# COHERE_API_KEY = "<use-your-own>"

headers = {
    "X-AWS-Access-Key": "<use-your-own>",
    "X-AWS-Secret-Key": "<use-your-own>",
    "X-AWS-Session-Token": "<use-your-own>"  # using this as I've temp creds, ref: https://github.com/weaviate/weaviate/issues/4558
}

# client.close()
client = weaviate.connect_to_wcs(
    cluster_url=WCS_URL,                       
    auth_credentials=AuthApiKey(WEAVIATE_API_KEY),
    headers=headers,
    additional_config=AdditionalConfig(
        timeout=Timeout(init=2, query=120, insert=120)  # embedded the entire dataset, sometimes it lead to timeouts with generative queries
    )
)

print(client.is_ready(), json.dumps(client.get_meta()))

# COMMAND ----------

# deleting the exisitng collection if it exists already, to create a new one later
# if client.collections.exists("JobPostings"):
#   client.collections.delete("JobPostings")

client.collections.create(
  "JobPostings",
  vectorizer_config=Configure.Vectorizer.text2vec_aws(
    region="us-east-1",
    service="bedrock",
    model="cohere.embed-multilingual-v3",  # not sure if all the jobs are in English, so using the multilingual model here
  ),
  # [ 
  #   # using named vectors was exponentially increasing the number of dimensions and was taking a lot of time too
  #   # I also noticed that named vectors do not seem to work with vector_index_config
  #
  #   Configure.NamedVectors.text2vec_aws(
  #     name="title",
  #     region="us-east-1",
  #     source_properties=["title"],
  #     service="bedrock",
  #     model="cohere.embed-multilingual-v3",
  #   ),
  #   Configure.NamedVectors.text2vec_aws(
  #     name="description",
  #     region="us-east-1",
  #     source_properties=["description"],
  #     service="bedrock",
  #     model="cohere.embed-multilingual-v3",
  #   ),
  # ],
  vector_index_config=Configure.VectorIndex.hnsw(),  # recently learned about this in the deeplearning.ai + weaviate course and seems to be most promising for this large dataset
  generative_config=Configure.Generative.aws(  # to allow the user to ask questions based on the search responses returned
    region="us-east-1",
    model="anthropic.claude-3-sonnet-20240229-v1:0"
  )
)

# COMMAND ----------

# ingestion

job_postings_collection = client.collections.get("JobPostings")

# no need to re-run with weavaite cloud, took 1-2 hours at first

with job_postings_collection.batch.dynamic() as batch:
  for job_posting in postings_json:
    batch.add_object(
      properties=job_posting,
    )

# COMMAND ----------

# MAGIC %md
# MAGIC **Utils**

# COMMAND ----------

count = job_postings_collection.aggregate.over_all(total_count=True)
print("Total items: ", count)

top_job_title = job_postings_collection.aggregate.over_all(
  return_metrics=Metrics("title").text(
    top_occurrences_count=True,
    top_occurrences_value=True,
    min_occurrences=2,
  )
)
print("Top job title: ", top_job_title)


# COMMAND ----------

def query_job_postings(collection_name: str, query: str, prompt: str=None, limit: int=50) -> str:
  """
  Performs either hybrid or generative search based on user request.

  Parameters
  ----------
  collection name : str
    Name of the collection

  query : str
    User query keywords.

  prompt : str
    Additonal question that the user can ask on top of the search responses.

  limit : int
    Number of search responses to return.
  
  Returns
  -------
  str
    Either the search results or the generated response by the LLM.

  """
  collection = client.collections.get(collection_name)

  if prompt:  # if the user included a prompt in the request, do a generative search to answer the question based on the search response
    response = collection.generate.hybrid(
      query=query,
      query_properties=["title", "location"],  # fields to use for keyword search
      grouped_task=prompt + " Only answer this based on the data provided above.",  # generation is performed on the search responses as a group, not on individual items in the response.
      # grouped_properties=["title"],
      limit=limit,
      alpha=0.75,  # want to favour the vector search more here
    )
  else:
    response = collection.query.hybrid(
      query=query,
      query_properties=["title", "location"], 
      limit=limit,
      alpha=0.75,
    )

  return response

# COMMAND ----------

# MAGIC %md
# MAGIC **Results**

# COMMAND ----------

# Example 1 - Semantic Search

response = query_job_postings(collection_name="JobPostings", query="Machine Learning Engineer, Software Engineer, Data Engineer", limit=100)

res = []
for res_job in response.objects:
  res.append([res_job.properties["title"], res_job.properties["company_name"], res_job.properties["formatted_date"]])

display(pd.DataFrame(res, columns=["title", "company_name", "date"]))

# COMMAND ----------

# Example 2 - Semantic Search

response = query_job_postings(collection_name="JobPostings", query="Dietician, Nutritionist", limit=100)

res = []
for res_job in response.objects:
  res.append([res_job.properties["title"], res_job.properties["company_name"], res_job.properties["location"]])

display(pd.DataFrame(res, columns=["title", "company_name", "location"]))

# COMMAND ----------

# Example 3 - Generative Search

response = query_job_postings(
  collection_name="JobPostings",
  query="Machine Learning Engineer, Data Scientist, Artificial Intelligence, Applied Scientist",
  prompt="Which location has the most AI/ML jobs?",
  limit=25
)

print(response.generated)

# COMMAND ----------

# Example 4 - Generative Search

response = query_job_postings(
  collection_name="JobPostings",
  query="Healthcare, Medicine",
  prompt="What is the average salary for the above included jobs? Also, which is the most frequent title for jobs in this domain?",
  limit=50
)

print(response.generated)

# COMMAND ----------

# Example 5 - Generative Search

response = query_job_postings(
  collection_name="JobPostings",
  query="Healthcare, Medicine",
  prompt="Are there any healthcare jobs in California? If yes, which city are they based in? Are any of them based in Irvine?",
  limit=50
)

print(response.generated)

# COMMAND ----------

# MAGIC %md
# MAGIC END

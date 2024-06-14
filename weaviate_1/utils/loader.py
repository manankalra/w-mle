import json
from pyspark.sql import SparkSession

# spark = SparkSession.builder.appName("Loader").getOrCreate()


def load(path, columns, fill_values=None):
    # df = spark.read.format("json").load(path).select(*columns)

    # if fill_values:
    #     df = df.fillna(fill_values)
    #
    # df_arr = [json.loads(row) for row in df.toJSON().collect()]

    return ""


# df = load(
#     path="../data/arxiv.json",
#     columns=[
#         "title",
#         "abstract",
#         "authors",
#         "categories",
#         "comments",
#         "journal-ref",
#         "update_date"],
#     fill_values={
#     "journal-ref": " ",
#     "comments": " ",
#     }
# )

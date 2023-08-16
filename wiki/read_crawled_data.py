from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://localhost:27017/")
db = client["wiki"]
col = db["wiki_math"]

print("num of docs: ", col.count_documents({}))

# col.delete_many({})

# myquery = {"key": "Mathematics"}
# mydoc = col.find(myquery)
# for x in mydoc:
#   print(x)


# mydoc = col.find({})
# df_drug = pd.DataFrame(list(mydoc))
# print(df_drug.head())
# print(df_drug.shape)
# print(df_drug.columns)
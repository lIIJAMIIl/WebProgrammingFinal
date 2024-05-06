# Creating a Mongita DB with Comment Info
import json
from mongita import MongitaClientDisk

# Writing the data to a Mongita DB file
# Create Mongita Client connection
client = MongitaClientDisk()

# create a comments DB
comments_db = client.comments_db

# create a comments collection
comments_collection = comments_db.comments_collection

# empty collection 
comments_collection.delete_many({})

#print quotes
print("Comments db created successfully")
print(comments_collection.count_documents({}))

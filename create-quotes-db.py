# Creating a Mongita DB with Quote Info
import json
from mongita import MongitaClientDisk

quotes_data = [
                {
                        "text":"I enjoy front-end development",
                        "author": "Josh Romisher",
                        "public": True
                },
                {
                        "text": "I like walks and tug of war.",
                        "author": "Rosie",
                        "public": True
                }
]

# Writing the data to a Mongita DB file
# Create Mongita Client connection
client = MongitaClientDisk()

# create a quotes DB
quotes_db = client.quotes_db

# create a quotes collection
quotes_collection = quotes_db.quotes_collection

# empty collection 
quotes_collection.delete_many({})

# inserting dictionary of quotes into DB
quotes_collection.insert_many(quotes_data)

#print quotes
print(quotes_collection.count_documents({}))

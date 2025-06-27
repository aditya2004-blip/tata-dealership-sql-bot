import os 
import pandas as pd
from pymongo import MongoClient 



mongo_url=os.getenv("MONGODB_URL")
client=MongoClient(mongo_url)

db=client['dealership_db']
folder_path="C:/Users/DELL/Desktop/Rag Bot/Dealership Data"

for file_name in os.listdir(folder_path):
    if file_name.endswith('.csv') or file_name.endswith('.xlsx'):
        state_name=file_name.split(" ")[0].lower()
        file_path=os.path.join(folder_path,state_name) 

        if(file_path.endswith('.csv')):
            df=pd.read_csv(file_path)
        else:
            df=pd.read_excel(file_path)

    dict_records=df.to_dict(orient="records")
    collection=db[state_name]
    collection.insert_many(dict_records)

    print(f"The Data saved for the {state_name}")
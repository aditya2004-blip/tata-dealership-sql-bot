# import os
# from pymongo import MongoClient
# import json

# # ---- All Indian states for matching ----
# INDIAN_STATES = [
#     "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa",
#     "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka", "kerala",
#     "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
#     "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
#     "uttar pradesh", "uttarakhand", "west bengal", "delhi", "jammu and kashmir",
#     "ladakh", "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli",
#     "daman and diu", "lakshadweep", "puducherry"
# ]

# def extract_state_from_query(query):
#     """Find state name in the query text. Returns title case match, or None."""
#     q = query.lower()
#     for state in INDIAN_STATES:
#         if state in q:
#             return state.title()
#     return None

# def get_sample_record_for_state(db, state_name):
#     """Fetch up to 5 records for a state, return the first (without _id), or None."""
#     doc = db.dealers.find_one({"Region": {"$regex": f"^{state_name}$", "$options": "i"}})
#     if doc:
#         doc.pop("_id", None)
#         return doc
#     return None

# def get_schema_context(query=None, mongo_url=None):
#     """
#     Returns a context string with schema description and, if possible, a sample record for a detected state.
#     If mongo_url is None, uses the env variable 'MONGODB_URL'.
#     If query is None, only static context is returned.
#     """
#     # --- Static schema rules ---
#     schema_context = """
# Table: dealers
# The schema is dynamically based on the actual structure observed for the relevant state.

# Instructions:
# - Use exact column names from the database record.
# - Dealer_ID format varies per state (e.g., 'OD-0001', 'GUJ-001', etc.).
# - When user query includes a dealer number (e.g., "dealer 5"), match both Dealer_ID and Dealer_Name fields.
# - Use LIKE with % for partial matches (e.g., Dealer_Name LIKE '%Odisha%Dealer%5%').
# - Always match the Region field for the intended state.
# """
#     # --- If no query, return static only ---
#     if not query:
#         return schema_context

#     # --- If state present in query, add a real sample record ---
#     state = extract_state_from_query(query)
#     print(f"State is {state}")
#     if not state:
#         return schema_context  # No state context available

#     # Connect to MongoDB
#     if not mongo_url:
#         mongo_url = os.getenv("MONGODB_URL")
#     if not mongo_url:
#         raise ValueError("MongoDB URL not provided")

#     client = MongoClient(mongo_url)
#     db = client['dealership_db']

#     record = get_sample_record_for_state(db, state)
#     if record:
#         schema_context += "\n\nExample record from the database for this state:\n"
#         schema_context += json.dumps(record, indent=2)
        
#     return schema_context



import os
from pymongo import MongoClient
import json

# ---- All Indian states for matching ----
INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa",
    "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka", "kerala",
    "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
    "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
    "uttar pradesh", "uttarakhand", "west bengal", "delhi", "jammu and kashmir",
    "ladakh", "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli",
    "daman and diu", "lakshadweep", "puducherry"
]

def format_state_to_collection(state):
    return state.strip().lower().replace(" ", "_") + "_dealership_data.csv"

def find_states_in_query(query, collection_names):
    q = query.lower()
    matched_collections = []
    for state in INDIAN_STATES:
        if state in q:
            coll_name = format_state_to_collection(state)
            if coll_name in collection_names:
                matched_collections.append(coll_name)
    print(f"[DEBUG] Matched state collections for query '{query}': {matched_collections}")
    return matched_collections

def get_schema_context(query=None, mongo_url=None):
    print(f"[DEBUG] Query: {query}")
    schema_context = """
Table: dealers

This is a dynamic schema derived from real data records for the relevant Indian states.

---
INSTRUCTIONS:
1. Use the table dealers only  
2. Use exact column names as per the sample schema below.
3. Do NOT use any column like `Region` unless it's clearly shown in the sample schema for that state.
4. If query contains multiple states, handle each separately and combine using `UNION ALL`. Ensure all subqueries are **aliased** (e.g., `AS result1`, `AS result2`, etc.).
5. Use `LIKE` only for partial matches (e.g., `Dealer_Name LIKE '%Dealer%'`). Do not use `LIKE` for numeric filters.
6. If the query refers to a dealer number (e.g., "dealer 5") and sample schema shows `Dealer_ID = 'OD-0005'`, then use:
   - `Dealer_ID LIKE '%OD-0005%'`
   - or `Dealer_Name LIKE '%Dealer 5%'`
   Match the prefix and padding from sample.
7. Use `LIMIT` instead of `TOP`. All subqueries must be syntactically correct DuckDB SQL.
8. NEVER guess column names. Use only what’s in the sample schema.
9. Always return ONLY the final SQL query. No explanation or notes.

---
SCHEMA SAMPLE AND DATA:
"""

    if not query:
        print("[DEBUG] No query provided, returning base schema context.")
        return schema_context

    # Connect to MongoDB
    if not mongo_url:
        mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        raise ValueError("MongoDB URL not provided")
    client = MongoClient(mongo_url)
    db = client['dealership_db']

    # Get all collection names
    collection_names = db.list_collection_names()
    print(f"[DEBUG] Available Mongo collections: {collection_names}")

    matched_collections = find_states_in_query(query, collection_names)
    if not matched_collections:
        print("[DEBUG] No matched collections, returning base schema context.")
        return schema_context

    # For each matched collection, fetch sample records and infer columns
    for coll in matched_collections:
        docs = list(db[coll].find({}, {"_id": 0}).sort("_id", -1).limit(3))
        if docs:
            columns = list(docs[0].keys())
            schema_context += f"\n\n🔹 Sample schema for collection '{coll}':\nColumns: {columns}\n"

            if "Region" in columns:
                schema_context += "- ✅ This schema includes a `Region` field. You may filter using it.\n"
            else:
                schema_context += "- ⚠️ This schema does NOT include a `Region` field. DO NOT use it.\n"

            schema_context += "\n🔸 Sample records:\n"
            for doc in docs:
                schema_context += json.dumps(doc, indent=2) + "\n"
        else:
            schema_context += f"\n\n⚠️ No records found for collection '{coll}'.\n"

    return schema_context

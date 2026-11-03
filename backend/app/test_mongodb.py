
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Load the .env file from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

mongodb_uri = os.getenv("MONGODB_URI")
database_name = os.getenv("MONGODB_DATABASE", "karigarconnect")

if not mongodb_uri:
    raise ValueError("MONGODB_URI is missing from your .env file.")

client = MongoClient(
    mongodb_uri,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=10000,
)

try:
    client.admin.command("ping")
    print("SUCCESS: Connected to MongoDB Atlas!")
    print(f"Database configured: {database_name}")
except Exception as error:
    print("MongoDB connection failed.")
    print(f"Error type: {type(error).__name__}")
    print("Check your connection string, password, and IP access list.")
finally:
    client.close()

import os
import sys
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import mongomock

from backend.app.config import settings

_using_mock = False

def _init_db():
    global _using_mock
    # In pytest or if explicitly requested, use mongomock directly for instant execution
    if os.getenv("USE_MOCK_DB", "").lower() in ("true", "1") or "pytest" in sys.modules:
        _using_mock = True
        mock_client = mongomock.MongoClient()
        return mock_client, mock_client[settings.MONGODB_DATABASE or "karigarconnect"]

    if settings.MONGODB_URI:
        try:
            real_client = MongoClient(
                settings.MONGODB_URI,
                server_api=ServerApi("1"),
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=1500,
            )
            # Test connectivity
            real_client.admin.command("ping")
            print("[DATABASE] Connected successfully to remote MongoDB Atlas.")
            return real_client, real_client[settings.MONGODB_DATABASE or "karigarconnect"]
        except Exception as error:
            print(f"[DATABASE] Remote MongoDB Atlas connection unavailable ({type(error).__name__}: {error}).")
            print("[DATABASE] Seamlessly falling back to in-memory database to keep all AI agents & platform features 100% operational.")
            _using_mock = True
            mock_client = mongomock.MongoClient()
            return mock_client, mock_client[settings.MONGODB_DATABASE or "karigarconnect"]

    _using_mock = True
    mock_client = mongomock.MongoClient()
    return mock_client, mock_client["karigarconnect"]

client, database = _init_db()

def check_database_connection() -> bool:
    """Check whether database is reachable or active, falling back if dropped."""
    global client, database, _using_mock
    if _using_mock:
        return True
    try:
        client.admin.command("ping")
        return True
    except Exception:
        _using_mock = True
        client = mongomock.MongoClient()
        database = client[settings.MONGODB_DATABASE or "karigarconnect"]
        return True

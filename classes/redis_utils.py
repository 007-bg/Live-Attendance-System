import redis
import json

# Redis client for session management
redis_client = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,  # Automatically decode responses to strings
)

# Session key prefix
SESSION_KEY_PREFIX = "attendance:session:"


def get_session_key(class_id):
    """
    Generate Redis key for a specific class session.

    Args:
        class_id (str): Class ID

    Returns:
        str: Redis key for the class session
    """
    return f"{SESSION_KEY_PREFIX}{class_id}"


def set_active_session(class_id, session_data):
    """
    Store active session in Redis for a specific class.

    Args:
        class_id (str): Class ID
        session_data (dict): Session data containing sessionId, classId, startedAt, attendance
    """
    key = get_session_key(class_id)
    redis_client.set(key, json.dumps(session_data))


def get_active_session(class_id):
    """
    Retrieve active session from Redis for a specific class.

    Args:
        class_id (str): Class ID

    Returns:
        dict: Session data or None if no active session
    """
    key = get_session_key(class_id)
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def update_attendance(class_id, student_id, status):
    """
    Update attendance status for a student in the active session.

    Args:
        class_id (str): Class ID
        student_id (str): Student ID
        status (str): Attendance status ('present' or 'absent')

    Returns:
        dict: Updated session data or None if no active session
    """
    session = get_active_session(class_id)
    if session:
        if "attendance" not in session:
            session["attendance"] = {}
        session["attendance"][student_id] = status
        set_active_session(class_id, session)
        return session
    return None


def clear_active_session(class_id):
    """
    Clear the active session from Redis for a specific class.

    Args:
        class_id (str): Class ID
    """
    key = get_session_key(class_id)
    redis_client.delete(key)


def session_exists(class_id):
    """
    Check if an active session exists for a specific class.

    Args:
        class_id (str): Class ID

    Returns:
        bool: True if session exists, False otherwise
    """
    key = get_session_key(class_id)
    return redis_client.exists(key) > 0


def get_all_active_sessions():
    """
    Get all active sessions across all classes.

    Returns:
        dict: Dictionary mapping class_id to session data
    """
    pattern = f"{SESSION_KEY_PREFIX}*"
    keys = redis_client.keys(pattern)
    sessions = {}

    for key in keys:
        class_id = key.replace(SESSION_KEY_PREFIX, "")
        data = redis_client.get(key)
        if data:
            sessions[class_id] = json.loads(data)

    return sessions

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request
from models import User
from bson import ObjectId

# Secret key for JWT - in production, this should be in environment variables
SECRET_KEY = 'campustrade-secret-key-2024'
ALGORITHM = 'HS256'
TOKEN_EXPIRATION_HOURS = 24


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_token(user_id):
    """Generate a JWT token for a user"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token):
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user_from_token():
    """Get the current user from the JWT token in the Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        # Extract token from "Bearer <token>" format
        token = auth_header.split(' ')[1]
        payload = decode_token(token)

        if not payload:
            return None

        user = User.objects.get(id=ObjectId(payload['user_id']))
        return user
    except (IndexError, User.DoesNotExist):
        return None


def require_auth(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_token()
        if user is None:
            return {'error': 'Authentication required'}, 401

        # Add user to kwargs so the route can access it
        kwargs['current_user'] = user
        return f(*args, **kwargs)

    return decorated_function


def require_role(allowed_roles):
    """Decorator to require specific roles for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user_from_token()
            if user is None:
                return {'error': 'Authentication required'}, 401

            if user.role not in allowed_roles and 'Both' not in allowed_roles:
                if user.role != 'Both':
                    return {'error': 'Insufficient permissions'}, 403

            # Add user to kwargs so the route can access it
            kwargs['current_user'] = user
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def is_owner(user, resource):
    """Check if user owns a resource (for listings)"""
    if hasattr(resource, 'seller_id'):
        return str(resource.seller_id.id) == str(user.id)
    return False


def is_thread_participant(user, thread):
    """Check if user is a participant in a thread"""
    return str(user.id) in [str(thread.buyer_id.id), str(thread.seller_id.id)]

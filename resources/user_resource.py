from flask import request
from flask_restful import Resource
from models import User
from utils.auth_utils import hash_password, require_auth
from bson import ObjectId


class UserListResource(Resource):
    """Handle POST /api/users (registration)"""

    def post(self):
        """Create a new user account (registration)"""
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['name', 'email', 'password', 'role']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            # Validate role
            if data['role'] not in ['Buyer', 'Seller', 'Both']:
                return {'error': 'Invalid role. Must be Buyer, Seller, or Both'}, 400

            # Check if email already exists
            existing_user = User.objects(email=data['email']).first()
            if existing_user:
                return {'error': 'Email already registered'}, 400

            # Hash password
            hashed_password = hash_password(data['password'])

            # Create user
            user = User(
                name=data['name'],
                email=data['email'],
                password=hashed_password,
                role=data['role'],
                verified=data.get('verified', False)
            )
            user.save()

            return {
                'message': 'User created successfully',
                'user': user.to_dict()
            }, 201

        except Exception as e:
            return {'error': str(e)}, 400


class UserResource(Resource):
    """Handle GET /api/users/:userId"""

    @require_auth
    def get(self, user_id, current_user=None):
        """Get user profile information"""
        try:
            user = User.objects.get(id=ObjectId(user_id))

            # Users can view any profile
            return user.to_dict(), 200

        except User.DoesNotExist:
            return {'error': 'User not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

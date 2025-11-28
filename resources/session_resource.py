from flask import request
from flask_restful import Resource
from models import User
from utils.auth_utils import hash_password, verify_password, generate_token, require_auth


class SessionResource(Resource):
    """Handle POST /api/sessions (login) and DELETE /api/sessions (logout)"""

    def post(self):
        """User login - creates a session (JWT token)"""
        try:
            data = request.get_json()

            # Validate required fields
            if 'email' not in data or 'password' not in data:
                return {'error': 'Email and password are required'}, 400

            # Find user by email
            try:
                user = User.objects.get(email=data['email'])
            except User.DoesNotExist:
                return {'error': 'Invalid email or password'}, 401

            # Verify password
            if not verify_password(data['password'], user.password):
                return {'error': 'Invalid email or password'}, 401

            # Generate JWT token
            token = generate_token(user.id)

            return {
                'token': token,
                'user': user.to_dict(),
                'message': 'Login successful'
            }, 200

        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def delete(self, current_user=None):
        """User logout - invalidates the current session"""
        try:
            # With JWT, logout is handled client-side by removing the token
            # Server-side, we just confirm the user is authenticated
            return {
                'message': 'Logout successful. Please remove the token from client storage.'
            }, 200

        except Exception as e:
            return {'error': str(e)}, 400

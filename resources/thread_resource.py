from flask import request
from flask_restful import Resource
from models import Listing, ChatThread, User
from bson import ObjectId
from datetime import datetime
from utils.auth_utils import require_auth, require_role, is_owner, is_thread_participant


class ThreadListResource(Resource):
    """Handle GET /listings/:listingId/threads and POST /listings/:listingId/threads"""

    @require_auth
    def get(self, listing_id, current_user=None):
        """Get all threads for a listing (owner only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Only the listing owner can see all threads
            if not is_owner(current_user, listing):
                return {'error': 'Only the listing owner can view all threads'}, 403

            threads = ChatThread.objects(listing_id=listing).order_by('-last_activity_time')

            return {
                'threads': [thread.to_dict() for thread in threads]
            }, 200

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    @require_role(['Buyer', 'Both'])
    def post(self, listing_id, current_user=None):
        """Start a chat thread (buyers only)"""
        try:
            # Verify listing exists
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Use current authenticated user as buyer
            buyer = current_user

            # Check if thread already exists
            existing_thread = ChatThread.objects(
                listing_id=listing,
                buyer_id=buyer
            ).first()

            if existing_thread:
                return {'error': 'Thread already exists', 'thread': existing_thread.to_dict()}, 400

            # Create new thread
            thread = ChatThread(
                listing_id=listing,
                buyer_id=buyer,
                seller_id=listing.seller_id
            )
            thread.save()

            return thread.to_dict(), 201

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class ThreadResource(Resource):
    """Handle GET /listings/:listingId/threads/:threadId and PATCH /listings/:listingId/threads/:threadId"""

    @require_auth
    def get(self, listing_id, thread_id, current_user=None):
        """Get a specific thread (participants only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            thread = ChatThread.objects.get(id=ObjectId(thread_id), listing_id=listing)

            # Verify user is a participant
            if not is_thread_participant(current_user, thread):
                return {'error': 'Only thread participants can view this thread'}, 403

            return thread.to_dict(), 200

        except (Listing.DoesNotExist, ChatThread.DoesNotExist):
            return {'error': 'Listing or Thread not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def patch(self, listing_id, thread_id, current_user=None):
        """Update thread (participants only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            thread = ChatThread.objects.get(id=ObjectId(thread_id), listing_id=listing)

            # Verify user is a participant
            if not is_thread_participant(current_user, thread):
                return {'error': 'Only thread participants can update this thread'}, 403

            data = request.get_json()

            # Update last activity time
            thread.last_activity_time = datetime.utcnow()
            thread.save()

            return thread.to_dict(), 200

        except (Listing.DoesNotExist, ChatThread.DoesNotExist):
            return {'error': 'Listing or Thread not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class StandaloneThreadListResource(Resource):
    """Handle GET /threads"""

    @require_auth
    def get(self, current_user=None):
        """Get all threads for current user"""
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))

            # Use current authenticated user
            user = current_user

            # Find threads where user is buyer or seller
            skip = (page - 1) * per_page
            threads = ChatThread.objects(
                __raw__={
                    '$or': [
                        {'buyer_id': user.id},
                        {'seller_id': user.id}
                    ]
                }
            ).order_by('-last_activity_time').skip(skip).limit(per_page)

            total = ChatThread.objects(
                __raw__={
                    '$or': [
                        {'buyer_id': user.id},
                        {'seller_id': user.id}
                    ]
                }
            ).count()

            return {
                'threads': [thread.to_dict() for thread in threads],
                'page': page,
                'per_page': per_page,
                'total': total
            }, 200

        except Exception as e:
            return {'error': str(e)}, 400


class StandaloneThreadResource(Resource):
    """Handle GET /threads/:threadId"""

    @require_auth
    def get(self, thread_id, current_user=None):
        """Get a specific thread (participants only)"""
        try:
            thread = ChatThread.objects.get(id=ObjectId(thread_id))

            # Verify user is a participant
            if not is_thread_participant(current_user, thread):
                return {'error': 'Only thread participants can view this thread'}, 403

            return thread.to_dict(), 200
        except ChatThread.DoesNotExist:
            return {'error': 'Thread not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

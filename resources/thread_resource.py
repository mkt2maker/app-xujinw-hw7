from flask import request
from flask_restful import Resource
from models import Listing, ChatThread, User
from bson import ObjectId
from datetime import datetime


class ThreadListResource(Resource):
    """Handle GET /listings/:listingId/threads and POST /listings/:listingId/threads"""

    def get(self, listing_id):
        """Get all threads for a listing (owner only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            threads = ChatThread.objects(listing_id=listing).order_by('-last_activity_time')

            return {
                'threads': [thread.to_dict() for thread in threads]
            }, 200

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    def post(self, listing_id):
        """Start a chat thread (buyers only)"""
        try:
            data = request.get_json()

            # Validate required fields
            if 'buyer_id' not in data:
                return {'error': 'Missing required field: buyer_id'}, 400

            # Verify listing exists
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Verify buyer exists
            buyer = User.objects.get(id=ObjectId(data['buyer_id']))

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
        except User.DoesNotExist:
            return {'error': 'Buyer not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class ThreadResource(Resource):
    """Handle GET /listings/:listingId/threads/:threadId and PATCH /listings/:listingId/threads/:threadId"""

    def get(self, listing_id, thread_id):
        """Get a specific thread (participants only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            thread = ChatThread.objects.get(id=ObjectId(thread_id), listing_id=listing)

            return thread.to_dict(), 200

        except (Listing.DoesNotExist, ChatThread.DoesNotExist):
            return {'error': 'Listing or Thread not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    def patch(self, listing_id, thread_id):
        """Update thread (participants only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            thread = ChatThread.objects.get(id=ObjectId(thread_id), listing_id=listing)

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

    def get(self):
        """Get all threads for current user"""
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            user_id = request.args.get('user_id')  # In production, get from session

            if not user_id:
                return {'error': 'user_id parameter required'}, 400

            user = User.objects.get(id=ObjectId(user_id))

            # Find threads where user is buyer or seller
            skip = (page - 1) * per_page
            threads = ChatThread.objects(
                __raw__={
                    '$or': [
                        {'buyer_id': ObjectId(user_id)},
                        {'seller_id': ObjectId(user_id)}
                    ]
                }
            ).order_by('-last_activity_time').skip(skip).limit(per_page)

            total = ChatThread.objects(
                __raw__={
                    '$or': [
                        {'buyer_id': ObjectId(user_id)},
                        {'seller_id': ObjectId(user_id)}
                    ]
                }
            ).count()

            return {
                'threads': [thread.to_dict() for thread in threads],
                'page': page,
                'per_page': per_page,
                'total': total
            }, 200

        except User.DoesNotExist:
            return {'error': 'User not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class StandaloneThreadResource(Resource):
    """Handle GET /threads/:threadId"""

    def get(self, thread_id):
        """Get a specific thread"""
        try:
            thread = ChatThread.objects.get(id=ObjectId(thread_id))
            return thread.to_dict(), 200
        except ChatThread.DoesNotExist:
            return {'error': 'Thread not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

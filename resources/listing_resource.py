from flask import request
from flask_restful import Resource
from models import Listing, User
from bson import ObjectId
from datetime import datetime
from utils.auth_utils import require_auth, require_role, is_owner


class ListingListResource(Resource):
    """Handle GET /listings and POST /listings"""

    def get(self):
        """Get all published listings with pagination and filters"""
        try:
            # Get query parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            category = request.args.get('category')
            sort_by = request.args.get('sort_by', 'created_at')

            # Build query
            query = {'status': 'Published'}
            if category:
                query['category'] = category

            # Pagination
            skip = (page - 1) * per_page

            # Sort order
            sort_field = 'price' if sort_by == 'price' else '-created_at'

            listings = Listing.objects(**query).order_by(sort_field).skip(skip).limit(per_page)
            total = Listing.objects(**query).count()

            return {
                'listings': [listing.to_dict() for listing in listings],
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }, 200

        except Exception as e:
            return {'error': str(e)}, 400

    @require_role(['Seller', 'Both'])
    def post(self, current_user=None):
        """Create a new listing (sellers only)"""
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['title', 'price', 'category', 'condition']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            # Use current authenticated user as seller
            seller = current_user

            # Verify user has seller privileges
            if seller.role not in ['Seller', 'Both']:
                return {'error': 'User is not authorized to sell'}, 403

            # Create listing
            listing = Listing(
                seller_id=seller,
                title=data['title'],
                description=data.get('description', ''),
                price=float(data['price']),
                category=data['category'],
                condition=data['condition'],
                status=data.get('status', 'Draft')
            )
            listing.save()

            return listing.to_dict(), 201

        except Exception as e:
            return {'error': str(e)}, 400


class ListingResource(Resource):
    """Handle GET /listings/:id, PATCH /listings/:id, DELETE /listings/:id"""

    def get(self, listing_id):
        """Get a specific listing"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            return listing.to_dict(), 200
        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def patch(self, listing_id, current_user=None):
        """Update a listing (owner only)"""
        try:
            data = request.get_json()
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Verify the current user is the seller/owner
            if not is_owner(current_user, listing):
                return {'error': 'Only the listing owner can update this listing'}, 403

            # Update allowed fields
            if 'title' in data:
                listing.title = data['title']
            if 'description' in data:
                listing.description = data['description']
            if 'price' in data:
                listing.price = float(data['price'])
            if 'category' in data:
                listing.category = data['category']
            if 'condition' in data:
                listing.condition = data['condition']
            if 'status' in data:
                listing.status = data['status']

            listing.updated_at = datetime.utcnow()
            listing.save()

            return listing.to_dict(), 200

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def delete(self, listing_id, current_user=None):
        """Delete a listing (owner only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Verify the current user is the seller/owner
            if not is_owner(current_user, listing):
                return {'error': 'Only the listing owner can delete this listing'}, 403

            listing.delete()
            return {'message': 'Listing deleted successfully'}, 200
        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400
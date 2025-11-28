from flask import request
from flask_restful import Resource
from models import Review, Listing, User
from bson import ObjectId
from datetime import datetime
from utils.auth_utils import require_auth


class ReviewListResource(Resource):
    """Handle GET /reviews and POST /reviews"""

    def get(self):
        """Get all reviews (Admin only)"""
        try:
            # Get query parameters for pagination
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))

            # Pagination
            skip = (page - 1) * per_page

            reviews = Review.objects().order_by('-created_at').skip(skip).limit(per_page)
            total = Review.objects().count()

            return {
                'reviews': [review.to_dict() for review in reviews],
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }, 200

        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def post(self, current_user=None):
        """Create a new review (authenticated users only)"""
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['listing_id', 'reviewee_id', 'rating']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            # Verify listing exists
            listing = Listing.objects.get(id=ObjectId(data['listing_id']))

            # Use current authenticated user as reviewer
            reviewer = current_user

            # Verify reviewee exists
            reviewee = User.objects.get(id=ObjectId(data['reviewee_id']))

            # Validate rating is between 1-5
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                return {'error': 'Rating must be between 1 and 5'}, 400

            # Check if review already exists for this listing by this reviewer
            existing_review = Review.objects(
                listing_id=listing,
                reviewer_id=reviewer
            ).first()

            if existing_review:
                return {'error': 'You have already reviewed this listing'}, 400

            # Create review
            review = Review(
                listing_id=listing,
                reviewer_id=reviewer,
                reviewee_id=reviewee,
                rating=rating,
                comment=data.get('comment', '')
            )
            review.save()

            return review.to_dict(), 201

        except (Listing.DoesNotExist, User.DoesNotExist):
            return {'error': 'Listing or User not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class ReviewResource(Resource):
    """Handle GET /reviews/:reviewId, PATCH /reviews/:reviewId, DELETE /reviews/:reviewId"""

    def get(self, review_id):
        """Get a specific review"""
        try:
            review = Review.objects.get(id=ObjectId(review_id))
            return review.to_dict(), 200
        except Review.DoesNotExist:
            return {'error': 'Review not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def patch(self, review_id, current_user=None):
        """Update review (helpful count or moderation status) - authenticated users"""
        try:
            review = Review.objects.get(id=ObjectId(review_id))
            data = request.get_json()

            # Update allowed fields
            if 'helpful_count' in data:
                review.helpful_count = int(data['helpful_count'])
            if 'is_flagged' in data:
                review.is_flagged = data['is_flagged']
            if 'moderation_status' in data:
                if data['moderation_status'] in ['Pending', 'Approved', 'Rejected']:
                    review.moderation_status = data['moderation_status']
                else:
                    return {'error': 'Invalid moderation status'}, 400

            review.updated_at = datetime.utcnow()
            review.save()

            return review.to_dict(), 200

        except Review.DoesNotExist:
            return {'error': 'Review not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    @require_auth
    def delete(self, review_id, current_user=None):
        """Delete a review (soft delete by marking as rejected) - admin/authenticated users"""
        try:
            review = Review.objects.get(id=ObjectId(review_id))

            # Soft delete: mark as rejected instead of actually deleting
            review.moderation_status = 'Rejected'
            review.is_flagged = True
            review.updated_at = datetime.utcnow()
            review.save()

            return {'message': 'Review deleted successfully'}, 200
        except Review.DoesNotExist:
            return {'error': 'Review not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class ListingReviewListResource(Resource):
    """Handle GET /listings/:listingId/reviews"""

    def get(self, listing_id):
        """Get all reviews for a listing"""
        try:
            # Verify listing exists
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Get only approved reviews
            reviews = Review.objects(
                listing_id=listing,
                moderation_status='Approved'
            ).order_by('-created_at')

            return {
                'reviews': [review.to_dict() for review in reviews]
            }, 200

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class UserReviewListResource(Resource):
    """Handle GET /users/:userId/reviews"""

    def get(self, user_id):
        """Get all reviews received by a user"""
        try:
            # Verify user exists
            user = User.objects.get(id=ObjectId(user_id))

            # Get all approved reviews for this user
            reviews = Review.objects(
                reviewee_id=user,
                moderation_status='Approved'
            ).order_by('-created_at')

            # Calculate average rating
            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews) if len(reviews) > 0 else 0

            return {
                'reviews': [review.to_dict() for review in reviews],
                'total_reviews': len(reviews),
                'average_rating': round(avg_rating, 2)
            }, 200

        except User.DoesNotExist:
            return {'error': 'User not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

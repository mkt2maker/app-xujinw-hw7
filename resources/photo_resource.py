from flask import request
from flask_restful import Resource
from models import Listing, ListingPhoto
from bson import ObjectId


class PhotoListResource(Resource):
    """Handle GET /listings/:listingId/photos and POST /listings/:listingId/photos"""

    def get(self, listing_id):
        """Get all photos for a listing"""
        try:
            # Verify listing exists
            listing = Listing.objects.get(id=ObjectId(listing_id))

            photos = ListingPhoto.objects(listing_id=listing).order_by('display_order')
            return {
                'photos': [photo.to_dict() for photo in photos]
            }, 200

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    def post(self, listing_id):
        """Add a photo to a listing (owner only)"""
        try:
            data = request.get_json()

            # Validate required fields
            if 'photo_url' not in data:
                return {'error': 'Missing required field: photo_url'}, 400

            # Verify listing exists
            listing = Listing.objects.get(id=ObjectId(listing_id))

            # Get the next display order
            existing_photos = ListingPhoto.objects(listing_id=listing).count()

            photo = ListingPhoto(
                listing_id=listing,
                photo_url=data['photo_url'],
                display_order=data.get('display_order', existing_photos)
            )
            photo.save()

            return photo.to_dict(), 201

        except Listing.DoesNotExist:
            return {'error': 'Listing not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400


class PhotoResource(Resource):
    """Handle PATCH /listings/:listingId/photos/:photoId and DELETE /listings/:listingId/photos/:photoId"""

    def patch(self, listing_id, photo_id):
        """Update photo order (owner only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            photo = ListingPhoto.objects.get(id=ObjectId(photo_id), listing_id=listing)

            data = request.get_json()
            if 'display_order' in data:
                photo.display_order = int(data['display_order'])
                photo.save()

            return photo.to_dict(), 200

        except (Listing.DoesNotExist, ListingPhoto.DoesNotExist):
            return {'error': 'Listing or Photo not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400

    def delete(self, listing_id, photo_id):
        """Remove a photo (owner only)"""
        try:
            listing = Listing.objects.get(id=ObjectId(listing_id))
            photo = ListingPhoto.objects.get(id=ObjectId(photo_id), listing_id=listing)
            photo.delete()

            return {'message': 'Photo deleted successfully'}, 200

        except (Listing.DoesNotExist, ListingPhoto.DoesNotExist):
            return {'error': 'Listing or Photo not found'}, 404
        except Exception as e:
            return {'error': str(e)}, 400
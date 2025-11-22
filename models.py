from mongoengine import Document, StringField, FloatField, DateTimeField, ReferenceField, IntField, BooleanField
from datetime import datetime


class User(Document):
    """User model representing both buyers and sellers"""
    meta = {'collection': 'users'}

    name = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True)
    role = StringField(required=True, choices=['Buyer', 'Seller', 'Both'])
    verified = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'verified': self.verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Listing(Document):
    """Listing model for items being sold"""
    meta = {'collection': 'listings'}

    seller_id = ReferenceField(User, required=True)
    title = StringField(required=True, max_length=200)
    description = StringField(max_length=1000)
    price = FloatField(required=True, min_value=0)
    category = StringField(
        required=True,
        choices=['Textbooks', 'Electronics', 'Dorm Supplies', 'Furniture', 'Clothing', 'Other']
    )
    condition = StringField(
        required=True,
        choices=['New', 'Like New', 'Good', 'Fair', 'Poor']
    )
    status = StringField(
        required=True,
        default='Draft',
        choices=['Draft', 'Published', 'Sold']
    )
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'seller_id': str(self.seller_id.id),
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'condition': self.condition,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ListingPhoto(Document):
    """Photo model for listing images"""
    meta = {'collection': 'listing_photos'}

    listing_id = ReferenceField(Listing, required=True)
    photo_url = StringField(required=True, max_length=500)
    uploaded_at = DateTimeField(default=datetime.utcnow)
    display_order = IntField(required=True, default=0)

    def to_dict(self):
        return {
            'id': str(self.id),
            'listing_id': str(self.listing_id.id),
            'photo_url': self.photo_url,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'display_order': self.display_order
        }


class ChatThread(Document):
    """Chat thread model for buyer-seller communication"""
    meta = {'collection': 'chat_threads'}

    listing_id = ReferenceField(Listing, required=True)
    buyer_id = ReferenceField(User, required=True)
    seller_id = ReferenceField(User, required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    last_activity_time = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'listing_id': str(self.listing_id.id),
            'buyer_id': str(self.buyer_id.id),
            'seller_id': str(self.seller_id.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity_time': self.last_activity_time.isoformat() if self.last_activity_time else None
        }


class Review(Document):
    """Review model for transaction feedback"""
    meta = {'collection': 'reviews'}

    listing_id = ReferenceField(Listing, required=True)
    reviewer_id = ReferenceField(User, required=True)
    reviewee_id = ReferenceField(User, required=True)
    rating = IntField(required=True, min_value=1, max_value=5)
    comment = StringField(max_length=1000)
    helpful_count = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    is_flagged = BooleanField(default=False)
    moderation_status = StringField(
        required=True,
        default='Pending',
        choices=['Pending', 'Approved', 'Rejected']
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'listing_id': str(self.listing_id.id),
            'reviewer_id': str(self.reviewer_id.id),
            'reviewee_id': str(self.reviewee_id.id),
            'rating': self.rating,
            'comment': self.comment,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_flagged': self.is_flagged,
            'moderation_status': self.moderation_status
        }


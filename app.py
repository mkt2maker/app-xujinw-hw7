from flask import Flask
from flask_restful import Api
from mongoengine import connect
from utils.json_encoder import MongodbJSONProvider

# Import resources
from resources.listing_resource import (
    ListingListResource,
    ListingResource
)
from resources.photo_resource import (
    PhotoListResource,
    PhotoResource
)
from resources.thread_resource import (
    ThreadListResource,
    ThreadResource,
    StandaloneThreadListResource,
    StandaloneThreadResource
)
from resources.review_resource import (
    ReviewListResource,
    ReviewResource,
    ListingReviewListResource,
    UserReviewListResource
)
from resources.session_resource import SessionResource
from resources.user_resource import UserListResource, UserResource

app = Flask(__name__)

# Use custom JSON provider
app.json = MongodbJSONProvider(app)

# Initialize MongoDB connection
connect(
    db='campustrade',
    host='localhost',
    port=27017
)

# Initialize Flask-RESTful
api = Api(app)

# ============================================================================
# API Routes
# ============================================================================

# Authentication Endpoints
api.add_resource(SessionResource, '/api/sessions')

# User Endpoints
api.add_resource(UserListResource, '/api/users')
api.add_resource(UserResource, '/api/users/<string:user_id>')

# Main Listing Endpoints
api.add_resource(ListingListResource, '/api/listings')
api.add_resource(ListingResource, '/api/listings/<string:listing_id>')

# Listing Photo Endpoints
api.add_resource(PhotoListResource, '/api/listings/<string:listing_id>/photos')
api.add_resource(PhotoResource, '/api/listings/<string:listing_id>/photos/<string:photo_id>')

# Chat Thread Endpoints (under listings)
api.add_resource(ThreadListResource, '/api/listings/<string:listing_id>/threads')
api.add_resource(ThreadResource, '/api/listings/<string:listing_id>/threads/<string:thread_id>')

# Standalone Thread Endpoints
api.add_resource(StandaloneThreadListResource, '/api/threads')
api.add_resource(StandaloneThreadResource, '/api/threads/<string:thread_id>')

# Review Endpoints
api.add_resource(ReviewListResource, '/api/reviews')
api.add_resource(ReviewResource, '/api/reviews/<string:review_id>')

# Listing Review Endpoints
api.add_resource(ListingReviewListResource, '/api/listings/<string:listing_id>/reviews')

# User Review Endpoints
api.add_resource(UserReviewListResource, '/api/users/<string:user_id>/reviews')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
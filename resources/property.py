from flask_restful import Resource, fields, marshal_with, reqparse
from flask_jwt_extended import jwt_required, current_user
from models import PropertyModel, db


resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'image':fields.String,
    'price': fields.Integer,
    'bedrooms': fields.Integer,
    'bathrooms': fields.Integer,
    'location': fields.String,
    'is_active': fields.Boolean
}

class Property(Resource):
    # create a new instance of reqparser
    parser = reqparse.RequestParser()
    parser.add_argument('name',type=str, required=True, help="Name is required")
    parser.add_argument('description',type=str, required=True, help="Description is required")
    parser.add_argument('image',type=str, required=True, help="image is required")
    parser.add_argument('price', type=int, required=True, help=" price is required")
    parser.add_argument('bedrooms',type=int, required=True, help="bedrooms is required")
    parser.add_argument('bathrooms',type=int, required=True, help="bathrooms is required")
    parser.add_argument('location',type=str, required=True, help="location is required")
    parser.add_argument('is_active',type=bool, required=True, help="is_active is required")
    parser.add_argument('user_id',type=int, required=True, help="user_id is required")
    


    @marshal_with(resource_fields)
    @jwt_required()
    def get(self, id=None):
        if id:
            property = PropertyModel.query.filter_by(id=id).first()

            return property
        else:
            properties = PropertyModel.query.all()

            return properties

    # @jwt_required()
    def post(self):
        data = Property.parser.parse_args()
        user_id = data.get('user_id')  # Get the user_id from the request data

        # Ensure user_id is provided
        if user_id is None:
            return {"message": "User ID is required", "status": "fail"}, 400

        property = PropertyModel(**data)  # Create property without user_id

        try:
            db.session.add(property)
            db.session.commit()

            # Set the user_id for the property
            property.user_id = user_id

            return {"message": "Property created successfully", "status": "success"}
        except Exception as e:
            print(e)  # Print the specific error
            return {"message": "Unable to create property", "status": "fail" }

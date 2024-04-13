from flask_restful import Resource, fields, marshal_with, reqparse
from flask_jwt_extended import jwt_required, current_user
from models import PropertyModel, db


resource_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
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
    parser.add_argument('price', type=int, required=True, help=" price is required")
    parser.add_argument('bedrooms',type=int, required=True, help="bedrooms is required")
    parser.add_argument('bathrooms',type=int, required=True, help="bathrooms is required")
    parser.add_argument('location',type=str, required=True, help="location is required")
    parser.add_argument('is_active',type=bool, required=True, help="is_active is required")
    


    @marshal_with(resource_fields)
    @jwt_required()
    def get(self, id=None):
        if id:
            property = PropertyModel.query.filter_by(id=id).first()

            return property
        else:
            properties = PropertyModel.query.all()

            return properties

    @jwt_required()
    def post(self):
        # check if user is admin
        if current_user['role'] != 'admin':
            return {"message": "Unauthorized request", "status": "fail"}, 403

        data = Property.parser.parse_args()

        property = PropertyModel(**data)

        try:
            db.session.add(property)
            db.session.commit()

            return {"message": "Property created successfully", "status": "success"}
        except:
            return {"message": "Unable to create property", "status": "fail" }

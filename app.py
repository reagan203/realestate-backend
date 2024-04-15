import os
from datetime import timedelta
from flask_mail import Mail,Message
from flask import Flask,jsonify
from models import db, UserModel
from flask_restful import Api ,Resource, reqparse,fields, marshal_with
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token,create_refresh_token,jwt_required,get_jwt_identity
from resources.property import Property

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BUNDLE_ERRORS'] = True
app.config['SQLALCHEMY_ECHO'] = True
# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)


#flask mail set up ->
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'reaganm746@@gmail.com'
app.config['MAIL_PASSWORD'] = '123456'

# enable CORS
CORS(app)

# link migrations
migrations = Migrate(app, db)

# init our db
db.init_app(app)

# initialize flask restful
api = Api(app)

# initialize bcrypt
bcrypt = Bcrypt(app)
# initialize JWT
jwt = JWTManager(app)

# initialize flask mail
mail = Mail(app)

# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return UserModel.query.filter_by(id=identity).one_or_none().to_json()

class AppResource(Resource):
    def get(self):
        return "Welcome to the real estate api"



#user model set up 
user_fields = {
    'id': fields.Integer,
    'first_name': fields.String,
    'last_name': fields.String,
    'phone': fields.String,
    'email': fields.String,
    'role': fields.String,
    'created_at': fields.DateTime,
    'updated_at': fields.DateTime,
}

response_field = {
    "message": fields.String,
    "status": fields.String,
    "user": fields.Nested(user_fields)
}

def send_welcome_email(email, first_name):
    msg = Message("Welcome to our Real Estate Platform!", sender="your_email@gmail.com", recipients=[email])
    msg.body = f"Hello {first_name},\n\nWelcome to our Real Estate Platform. We're excited to have you on board!"
    mail.send(msg)

class Signup(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('first_name',type=str, required=True, help="Firstname is required")
    parser.add_argument('last_name',type=str, required=True, help="Last name is required")
    parser.add_argument('phone',type=str, required=True, help="Phone number is required")
    parser.add_argument('email',type=str, required=True, help="Email address is required")
    parser.add_argument('password',type=str, required=True, help="Password is required")
    parser.add_argument('role',type=str, required=False, help="Role is required")

    @marshal_with(response_field)
    def post(self):
        data = Signup.parser.parse_args()

        # encrypt password
        data['password'] = generate_password_hash(data['password'])
        # set default role
        data['role'] = 'member'

        user = UserModel(**data)

        # verify email and phone uniqueness before saving to the db
        email = UserModel.query.filter_by(email=data['email']).one_or_none()

        if email:
            return {"message": "Email already taken", "status": "fail"}, 400

        phone = UserModel.query.filter_by(phone=data['phone']).one_or_none()

        if phone:
            return {"message": "Phone number already exists", "status": "fail"}, 400

        try:
            # save user to db
            db.session.add(user)
            db.session.commit()
            # get user from db after saving
            db.session.refresh(user)

            user_json = user.to_json()
            access_token = create_access_token(identity=user_json['id'])
            refresh_token = create_refresh_token(identity=user_json['id'])

            # Call send_welcome_email function
            send_welcome_email(data['email'], data['first_name'])

            return {"message": "Account created successfully",
                    "status": "success",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user_json}, 201
        except:
            return {"message": "Unable to create account", "status": "fail"}, 400

        

class Login(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('email', required=True, help="Email address is required")
    parser.add_argument('password', required=True, help="Password is required")

    def post(self):
        data = Login.parser.parse_args()

        # 1. Get user using email
        user = UserModel.query.filter_by(email = data['email']).first()

        if user:
            # 2. check if provided password is correct
            is_password_correct = user.check_password(data['password'])

            if is_password_correct:
                # 3. Generate token and return user dict
                user_json = user.to_json()
                access_token = create_access_token(identity=user_json['id'])
                refresh_token = create_refresh_token(identity=user_json['id'])
                return {"message": "Login successful",
                        "status": "success",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": user_json,
                        }, 200
            else:
                return {"message": "Invalid email/password", "status": "fail"}, 403
        else:
            return {"message": "Invalid email/password", "status": "fail"}, 403

class RefreshAccess(Resource):
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()

        access_token = create_access_token(identity=identity)

        return jsonify(access_token = access_token)
    

#resource
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Property, '/property','/property/<int:id>')
api.add_resource(RefreshAccess, '/refresh-access')
    
    
    
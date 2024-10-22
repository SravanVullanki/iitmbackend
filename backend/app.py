from app import create_app, database_creator
from flask_cors import CORS

if __name__ == "__main__":
    app = create_app()  
    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})
    from flask_wtf.csrf import CSRFProtect
    # csrf = CSRFProtect(app)
    db_directory = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "") 
    database_creator(app, db_directory) 
    app.run(debug=True, port=4466, host='0.0.0.0')

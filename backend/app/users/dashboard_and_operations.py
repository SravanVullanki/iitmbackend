from datetime import datetime
from flask import Flask, app, Blueprint, render_template, session, redirect, url_for, request ,current_app
from itsdangerous import URLSafeTimedSerializer
from app.users.models import User
from app.users.admin.models import Service
from app.users.professional.models import Professional
from app.users.customer.models import ServiceRequest
from app.users.customer.models import Customer
from flask_bcrypt import Bcrypt
from flask import jsonify


import random
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask import flash
from app import db, enc
from flask import send_file, make_response
import io
from flask import send_file, Response
from flask import flash, redirect, request, session, url_for
from flask_mail import Mail, Message
from flask_cors import CORS

from werkzeug.security import check_password_hash, generate_password_hash


dash_blueprint = Blueprint("dash_blueprint", __name__)


CORS(dash_blueprint, resources={r"/*": {
    "origins": "http://localhost:8080",
    "allow_headers": ["Content-Type", "Authorization"],  # Explicitly allow headers
    "supports_credentials": True  # Enable credentials support (for sessions or cookies)
}})


bcrypt = Bcrypt()


mail = Mail()

def init_mail(app):
    mail.init_app(app)


from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send OTP')
    
def send_email(to, subject, body):
    with current_app.app_context():
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)


class AddServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    base_price = FloatField('Base Price', validators=[DataRequired()])
    professional_id = SelectField('Professional', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Service')



@dash_blueprint.route("/dashboard", methods=["GET"])
def dashboard():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session["user_id"]
    user = User.query.filter_by(user_id=user_id).first()

    if user.role == "admin":
        total_services = Service.query.count()
        new_professional_applications = Professional.query.filter_by(status="Pending").count()
        all_professional_count = Professional.query.count()
        total_requests = ServiceRequest.query.count()
        pending_requests = ServiceRequest.query.filter_by(status="Pending").count()

        pending_professionals = Professional.query.filter_by(status="Pending").all()
        all_professionals = Professional.query.filter(Professional.status != "Pending").all()

        return jsonify({
            "user": {
                "username": user.username,
                "role": user.role,
            },
            "stats": {
                "total_services": total_services,
                "new_professional_applications": new_professional_applications,
                "all_professional_count": all_professional_count,
                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "pending_professionals": [p.to_dict() for p in pending_professionals],
                "all_professionals": [p.to_dict() for p in all_professionals],
            }
        })

    elif user.role == "customer":
        customer = Customer.query.filter_by(user_id=user_id).first()

        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        service_requests = ServiceRequest.query.filter_by(customer_id=customer.customer_id).all()
        return jsonify({
            "customer_id": customer.customer_id,
            "service_requests": [sr.to_dict() for sr in service_requests],
        })

    elif user.role == "professional":
        professional = Professional.query.filter_by(user_id=user_id).first()

        if not professional:
            return jsonify({"error": "Professional profile not found"}), 404

        active_service_requests = ServiceRequest.query.filter(
            (ServiceRequest.professional_id == professional.professional_id) &
            (ServiceRequest.status.in_(["Pending", "Accepted"]))
        ).all()

        return jsonify({
            "active_service_requests": [sr.to_dict() for sr in active_service_requests],
        })

    return jsonify({"error": "Unauthorized"}), 401


@dash_blueprint.route("/dashboard/services", methods=["GET"])
def get_services():
    print("1")
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401


    services = Service.query.all()
    service_list = []
    service_list = [service.to_dict() for service in services]
    print(service_list)
    


    available_professionals = Professional.query.filter(
        Professional.status == "Accepted",
        Professional.flagged == "False",
        Professional.services_offered==None  
    ).all()


    professionals_list = [
        {"professional_id": p.professional_id, "username": p.user.username} 
        for p in available_professionals
    ]

    return jsonify({
        "services": service_list,
        "professionals": professionals_list
    })

@dash_blueprint.route("/dashboard/services/add", methods=["POST"])
def add_service():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    required_fields = ["name", "description", "base_price", "professional_id"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    assigned_professionals = db.session.query(Service.professional_id).distinct()
    available_professionals = Professional.query.filter(
        Professional.professional_id.notin_(assigned_professionals),
        Professional.status == "Accepted",
        Professional.flagged == "False"
    ).all()

    if not any(p.professional_id == data["professional_id"] for p in available_professionals):
        return jsonify({"error": "Selected professional is not available."}), 400

    new_service = Service(
        name=data["name"],
        description=data["description"],
        base_price=data["base_price"],
        professional_id=data["professional_id"]
    )
    db.session.add(new_service)
    db.session.commit()

    return jsonify({"message": "Service added successfully!"}), 201


@dash_blueprint.route("/dashboard/services/delete/<int:service_id>", methods=["DELETE"])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({"message": "Service deleted successfully!"}), 204

@dash_blueprint.route("/dashboard/services/edit/<int:service_id>", methods=["GET", "PUT"])
def edit_service(service_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    service = Service.query.get_or_404(service_id)

    if request.method == "PUT":
        data = request.get_json()
        
        service.name = data.get('name', service.name)  
        service.description = data.get('description', service.description)
        service.base_price = data.get('base_price', service.base_price)
        service.professional_id = data.get('professional_id', service.professional_id)

        db.session.commit()
        return jsonify({"message": "Service updated successfully!"}), 200

    professional = Professional.query.get(service.professional_id)
    professional_name = professional.user.username if professional else "Unknown"


    return jsonify({
        **service.to_dict(),
        "professional_name": professional_name  
    })


@dash_blueprint.route("/dashboard/professionals", methods=["GET", "POST"])
def professionals():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "POST":
        professional_id = request.json.get("professional_id")
        action = request.json.get("action")  

        professional = Professional.query.get(professional_id)

        if action == "accept":
            professional.status = "Accepted"
            send_email(professional.user.email, "Application Accepted", "Your application has been accepted.")
        elif action == "reject":
            professional.status = "Rejected"
            send_email(professional.user.email, "Application Rejected", "Your application has been rejected.")
        elif action == "flag":
            professional.flagged = "False" if professional.flagged == "True" else "True"
            send_email(professional.user.email, "You Have Been Flagged" if professional.flagged == "True" else "Flag Removed", 
                       "You have been flagged due to your actions. You will not be able to access Meto from now." if professional.flagged == "True" else "Your flag status has been removed. You can now access Meto again.")

        db.session.commit()
        return jsonify({"message": "Action completed successfully"}), 200

    pending_professionals = Professional.query.filter_by(status="Pending").all()
    all_professionals = Professional.query.filter(Professional.status != "Pending").all()

    return jsonify({
        "pending_professionals": [prof.to_dict() for prof in pending_professionals],
        "all_professionals": [prof.to_dict() for prof in all_professionals]
    }), 200


@dash_blueprint.route('/professionals/<int:professional_id>/resume', methods=['GET'])
def view_resume(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    
    if not professional.pdf_resume:
        return jsonify({"error": "No resume found for this professional"}), 404
    
    return Response(
        io.BytesIO(professional.pdf_resume),  
        mimetype='application/pdf',
        headers={"Content-Disposition": "inline; filename=resume.pdf"} 
    )


@dash_blueprint.route('/customers', methods=["GET", "POST"])
def customers():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    active_page = 'customers'
    if request.method == "POST":
        customer_id = request.json.get("customer_id")
        action = request.json.get("action")

        customer = Customer.query.get(customer_id) 

        if action == "flag":
            customer.flagged = "True" if customer.flagged == "False" else "False"
            flag_message = "You have been flagged." if customer.flagged == "True" else "Your flag has been removed."
            send_email(customer.user.email, "Flag Status Changed", flag_message)

        db.session.commit()
        return jsonify({"message": "Flag status updated successfully"}), 200

    customers = Customer.query.all()
    return jsonify({
        "customers": [cust.to_dict() for cust in customers]
    }), 200


@dash_blueprint.route('/service_requests', methods=["GET", "POST"])
def service_requests():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    # Handle JSON data from Vue.js
    data = request.get_json()
    
    search_category = data.get("search_category", "")
    search_term = data.get("search_term", "").strip().lower()

    query = ServiceRequest.query

    if search_category == "service" and search_term:
        query = query.join(Service).filter(Service.name.ilike(f"%{search_term}%"))
    elif search_category == "professional" and search_term:
        query = query.join(Professional).join(User).filter(User.username.ilike(f"%{search_term}%"))
    elif search_category == "customer" and search_term:
        query = query.join(Customer).join(User).filter(User.username.ilike(f"%{search_term}%"))

    service_requests = query.all()

    return jsonify({
        "service_requests": [req.to_dict() for req in service_requests],
        "active_page": "service_requests",
        "search_category": search_category,
        "search_term": search_term
    }), 200


from flask import jsonify, request

@dash_blueprint.route('/professional/home', methods=["GET"])
def professional_home():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session.get("user_id")
    professional = Professional.query.filter_by(user_id=user_id).first()

    if not professional:
        return jsonify({"error": "Professional profile not found."}), 404

    active_service_requests = ServiceRequest.query.filter(
        (ServiceRequest.professional_id == professional.professional_id) &
        (ServiceRequest.status.in_(["Pending", "Accepted"]))
    ).all()

    return jsonify({
        "active_service_requests": [request.to_dict() for request in active_service_requests]
    }), 200


@dash_blueprint.route('/professional/professional_profile', methods=['GET', 'POST'])
def professional_profile():
    
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    professional = Professional.query.filter_by(user_id=session["user_id"]).first()

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')
        


        stored_password = professional.user.password
        if isinstance(stored_password, bytes):
            stored_password = stored_password.decode('utf-8')

        if not stored_password:
            return jsonify({"error": "No password found in the system. Please contact support."}), 400

        if not bcrypt.check_password_hash(stored_password, current_password):
            return jsonify({"error": "Incorrect current password."}), 403

        if new_password and new_password != confirm_new_password:
            return jsonify({"error": "New passwords do not match."}), 400

        if new_password:
            professional.user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        if 'pdf_resume' in request.files:
            resume_file = request.files['pdf_resume']
            if resume_file and resume_file.filename.endswith('.pdf'):
                professional.pdf_resume = resume_file.read()

        db.session.commit()
        return jsonify({"message": "Credentials updated successfully!"}), 200

    return jsonify({
        "professional": professional.to_dict()  
    }), 200


@dash_blueprint.route('/professional/allservices', methods=["GET"])
def professional_allservices():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session.get("user_id")
    professional = Professional.query.filter_by(user_id=user_id).first()

    if not professional:
        return jsonify({"error": "Professional profile not found."}), 404

    assigned_service_requests = ServiceRequest.query.filter_by(professional_id=professional.professional_id).all()

    return jsonify({
        "assigned_service_requests": [request.to_dict() for request in assigned_service_requests]
    }), 200

from flask import jsonify, request

@dash_blueprint.route('/professional/activeservices', methods=['GET', 'POST'])
def professional_activeservices():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session.get("user_id")
    professional = Professional.query.filter_by(user_id=user_id).first()

    if not professional:
        return jsonify({"error": "Professional profile not found."}), 404

    active_service_requests = ServiceRequest.query.filter(
        (ServiceRequest.professional_id == professional.professional_id) &
        (ServiceRequest.status.in_(["Pending", "Accepted"]))
    ).all()

    if request.method == 'POST':
        request_id = request.json.get('request_id')
        action = request.json.get('action')
        otp_input = request.json.get('otp')  # OTP input from form

        service_request = ServiceRequest.query.get(request_id)

        if service_request and service_request.professional_id == professional.professional_id:
            if action == 'accept':
                service_request.status = 'Accepted'
                db.session.commit()
                return jsonify({"message": "Service request accepted successfully!"}), 200

            elif action == 'complete':
                if service_request.status == 'Accepted':  
                    if service_request.otp == otp_input:  # Verify OTP
                        service_request.status = 'Completed'
                        db.session.commit()
                        return jsonify({"message": "Service request completed successfully!"}), 200
                    else:
                        return jsonify({"error": "Invalid OTP. Please try again."}), 400
                else:
                    return jsonify({"error": "Service request must be accepted before completion."}), 400

            elif action == 'reject':
                service_request.status = 'Rejected'
                db.session.commit()
                return jsonify({"message": "Service request rejected successfully!"}), 200
        else:
            return jsonify({"error": "Invalid service request or action."}), 400

    return jsonify({
        "active_service_requests": [request.to_dict() for request in active_service_requests]
    }), 200

@dash_blueprint.route('/professional/summary', methods=['GET'])
def professional_summary():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session.get("user_id")
    professional = Professional.query.filter_by(user_id=user_id).first()

    if not professional:
        return jsonify({"error": "Professional profile not found."}), 404

    status_counts = {
        'completed':ServiceRequest.query.filter_by(professional_id=professional.professional_id, status='Completed').count(),
        'accepted': ServiceRequest.query.filter_by(professional_id=professional.professional_id, status='Accepted').count(),
        'rejected': ServiceRequest.query.filter_by(professional_id=professional.professional_id, status='Rejected').count(),
        'pending': ServiceRequest.query.filter_by(professional_id=professional.professional_id, status='Pending').count(),
    }

    service_counts = db.session.query(
        ServiceRequest.service_id,
        db.func.count(ServiceRequest.service_id)
    ).filter(ServiceRequest.professional_id == professional.professional_id).group_by(ServiceRequest.service_id).all()

    service_count_dict = {str(service_id): count for service_id, count in service_counts}

    average_ratings = db.session.query(
        ServiceRequest.service_id,
        db.func.avg(ServiceRequest.rating)  
    ).filter(ServiceRequest.professional_id == professional.professional_id).group_by(ServiceRequest.service_id).all()

    average_rating_dict = {str(service_id): round(avg_rating, 2) for service_id, avg_rating in average_ratings}

    return jsonify({
        "statusCounts": status_counts,
        "serviceCounts": service_count_dict,
        "averageRatings": [average_rating_dict.get(str(service_id), 0) for service_id in service_count_dict.keys()],  
    }), 200



@dash_blueprint.route('/customer/home', methods=['GET'])
def customer_home():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    customer_id = session.get("user_id")
    customer = Customer.query.filter_by(user_id=customer_id).first()

    if not customer:
        return jsonify({"error": "Customer not found."}), 404

    service_requests = ServiceRequest.query.filter_by(customer_id=customer.customer_id).all()

    return jsonify({
        "service_requests": [request.to_dict() for request in service_requests]
    }), 200


@dash_blueprint.route('/customer/rate_request/<int:request_id>', methods=['POST'])
def rate_request(request_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    rating = request.json.get('rating')
    
    # Debugging output
    print("Received rating:", rating)
    print("Type of rating:", type(rating))

    # Ensure that rating is a string and not None
    if rating is not None and isinstance(rating, str) and rating.isdigit():
        service_request = ServiceRequest.query.get(request_id)

        if service_request and service_request.status == 'Completed' and not service_request.rating:
            rating = int(rating)  # Convert the string to an integer
            service_request.rating = rating  
            db.session.commit()  

            professional = service_request.professional
            if professional:
                total_rating = (professional.rating * professional.rating_count) + rating
                professional.rating_count += 1
                professional.rating = total_rating / professional.rating_count

                db.session.commit()  

            return jsonify({"message": "Thank you for your feedback!"}), 200
        else:
            return jsonify({"error": "Invalid service request or rating already submitted."}), 400
    else:
        print("invalid")
        return jsonify({"error": "Invalid rating."}), 400



@dash_blueprint.route('/customer/delete_request/<int:request_id>', methods=['POST'])
def delete_request(request_id):
    service_request = ServiceRequest.query.get(request_id)

    if service_request:
        db.session.delete(service_request)
        db.session.commit()
        return jsonify({"message": "Service request deleted successfully!"}), 200
    else:
        return jsonify({"error": "Service request not found."}), 404


@dash_blueprint.route('/customer/services', methods=['GET'])
def customer_services():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401
    
    search_query = request.args.get('search', '')
    if search_query:
        services = Service.query.filter(
            (Service.name.ilike(f'%{search_query}%')) | 
            (Service.description.ilike(f'%{search_query}%'))
        ).all()
    else:
        services = Service.query.all()
    
    return jsonify({
        "services": [
            {
                **service.to_dict(),
                "base_price": float(service.base_price) if service.base_price is not None else None
            } for service in services
        ],
        "search_query": search_query
    }), 200

@dash_blueprint.route('/customer/complete_request/<int:request_id>', methods=['POST'])
def complete_request(request_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    service_request = ServiceRequest.query.get(request_id)

    if service_request and service_request.status != 'Completed':
        service_request.status = 'Completed'
        db.session.commit()
        return jsonify({"message": "Service request marked as completed."}), 200
    else:
        return jsonify({"error": "Invalid service request or it is already completed."}), 400

from datetime import datetime


@dash_blueprint.route('/customer/services/<int:service_id>', methods=['GET'])
def get_service_by_id(service_id):
    if not session.get("user_id"):
        return jsonify({'error': 'Unauthorized'}), 401

    service = Service.query.get(service_id)

    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    return jsonify({'service': service.to_dict()}), 200



@dash_blueprint.route('/customer/book_service/<int:service_id>', methods=['POST', 'GET'])
def book_service(service_id):
    if not session.get("user_id"):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session.get("user_id")
    customer = Customer.query.filter_by(user_id=user_id).first()
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    service = Service.query.get(service_id)
    
    if request.method == 'POST':
        professional_id = request.json.get('professional_id')
        service_date = request.json.get('service_date')
        service_time = request.json.get('service_time')

        service_datetime = datetime.strptime(f"{service_date} {service_time}", "%Y-%m-%d %H:%M")

        otp = "{:06}".format(random.randint(0, 999999))

        new_service_request = ServiceRequest(
            customer_id=customer.customer_id,
            service_id=service_id,
            status='Pending',
            request_date=datetime.utcnow(),
            service_date=service_datetime,
            professional_id=int(professional_id) if professional_id else None,
            otp=otp
        )

        db.session.add(new_service_request)
        db.session.commit()
        return jsonify({'message': 'Service request booked successfully!'}), 201

    return jsonify({'service': service.serialize()}), 200  


@dash_blueprint.route('/customer/history', methods=['GET'])
def customer_history():
    if not session.get("user_id"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    customer_id = session.get("user_id")
    customer = Customer.query.filter_by(user_id=customer_id).first()
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    service_history = ServiceRequest.query.filter_by(customer_id=customer.customer_id).all()
    
    return jsonify({'history': [request.to_dict() for request in service_history]}), 200  



@dash_blueprint.route('/customer/summary', methods=['GET'])
def customer_summary():
    if not session.get("user_id"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    customer_id = session.get("user_id")
    customer = Customer.query.filter_by(user_id=customer_id).first()

    service_requests = ServiceRequest.query.filter_by(customer_id=customer.customer_id).all()
    
    total_services = len(service_requests)
    ongoing_services = sum(1 for request in service_requests if request.status == 'Pending')
    
    # Extract ratings
    ratings = [request.rating for request in service_requests if request.rating is not None]
    average_rating = sum(ratings) / len(ratings) if ratings else 0

  
    booked_services = {}  
    for request in service_requests:
        request_date = request.request_date.isoformat() 
        if request_date not in booked_services:
            booked_services[request_date] = 0
        booked_services[request_date] += 1


    service_status = {}
    for request in service_requests:
        status = request.status
        if status not in service_status:
            service_status[status] = 0
        service_status[status] += 1

    summary = {
        "total_services": total_services,
        "ongoing_services": ongoing_services,
        "average_rating": average_rating,
        "ratings": ratings,
        "booked_services": [{"date": date, "count": count} for date, count in booked_services.items()],
        "service_status": service_status,
    }
    
    return jsonify({'summary': summary}), 200



@dash_blueprint.route('/customer/profile', methods=['GET', 'POST'])
def customer_profile():
    if not session.get("user_id"):
        return jsonify({'error': 'Unauthorized'}), 401

    customer = Customer.query.filter_by(user_id=session["user_id"]).first()

    if request.method == 'POST':
        current_password = request.json.get('current_password')
        new_password = request.json.get('new_password')
        confirm_new_password = request.json.get('confirm_new_password')
        username = request.json.get('username')
        email = request.json.get('email')
        phone_number = request.json.get('phone_number')
        address = request.json.get('address')

        stored_password = customer.user.password.decode('utf-8') if isinstance(customer.user.password, bytes) else customer.user.password
        
        if not bcrypt.check_password_hash(stored_password, current_password):
            return jsonify({'error': 'Incorrect current password.'}), 400

        if new_password and new_password != confirm_new_password:
            return jsonify({'error': 'New passwords do not match.'}), 400

        if username != customer.user.username and User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists. Please choose a different one.'}), 400

        if email != customer.user.email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists. Please choose a different one.'}), 400

        if phone_number != customer.phone_number and Customer.query.filter_by(phone_number=phone_number).first():
            return jsonify({'error': 'Phone number already exists. Please choose a different one.'}), 400

        if new_password:
            customer.user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        customer.user.username = username
        customer.phone_number = phone_number
        customer.user.email = email
        customer.address = address

        db.session.commit()
        return jsonify({'message': 'Profile updated successfully!'}), 200

    # Use to_dict instead of serialize
    return jsonify({'customer': customer.to_dict()}), 200

@dash_blueprint.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        otp = str(random.randint(100000, 999999))
        session['reset_otp'] = otp
        session['reset_email'] = email

        send_email(to=email, subject="Your OTP Code", body=f"Your OTP is: {otp}")  
        return jsonify({'message': 'An OTP has been sent to your email.'}), 200
    else:
        return jsonify({'error': 'Email not found.'}), 404


@dash_blueprint.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    entered_otp = data.get('otp')

    if entered_otp == session.get('reset_otp'):
        return jsonify({'message': 'OTP verified. Please reset your password.'}), 200
    else:
        return jsonify({'error': 'Invalid OTP. Please try again.'}), 400


@dash_blueprint.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    if new_password != confirm_new_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    email = session.get('reset_email')
    user = User.query.filter_by(email=email).first()

    if user:
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        return jsonify({'message': 'Password has been reset. You can now log in.'}), 200
    else:
        return jsonify({'error': 'User not found.'}), 404

@dash_blueprint.route('/admin_summary', methods=['GET'])
def admin_summary():
    flagged_count = db.session.query(Customer).filter(Customer.flagged == "True").count()
    not_flagged_count = db.session.query(Customer).filter(Customer.flagged == "False").count()

    flagged_professionals_count = db.session.query(Professional).filter(Professional.flagged == "True").count()
    not_flagged_professionals_count = db.session.query(Professional).filter(Professional.flagged == "False").count()

    professionals = db.session.query(Professional).all()
    professional_names = [p.expertise for p in professionals]
    professional_ratings = [p.rating for p in professionals]

    requests = db.session.query(ServiceRequest).all()
    request_categories = ['Pending', 'Completed', 'Rejected']
    request_ratings = [
        len([r for r in requests if r.status == 'Pending']),
        len([r for r in requests if r.status == 'Completed']),
        len([r for r in requests if r.status == 'Rejected']),
    ]

    return jsonify({
        'flagged_count': flagged_count,
        'not_flagged_count': not_flagged_count,
        'flagged_professionals_count': flagged_professionals_count,
        'not_flagged_professionals_count': not_flagged_professionals_count,
        'professional_names': professional_names,
        'professional_ratings': professional_ratings,
        'request_categories': request_categories,
        'request_ratings': request_ratings
    }), 200
import pdfkit
from datetime import datetime

@dash_blueprint.route('/download_report_pdf', methods=['GET'])
def download_report_pdf():
    flagged_customers_count = db.session.query(Customer).filter(Customer.flagged == "True").count()
    total_customers_count = db.session.query(Customer).count()
    flagged_professionals_count = db.session.query(Professional).filter(Professional.flagged == "True").count()
    total_professionals_count = db.session.query(Professional).count()
    pending_requests = db.session.query(ServiceRequest).filter(ServiceRequest.status == 'Pending').count()
    completed_requests = db.session.query(ServiceRequest).filter(ServiceRequest.status == 'Completed').count()
    rejected_requests = db.session.query(ServiceRequest).filter(ServiceRequest.status == 'Rejected').count()
    current_date = datetime.now().strftime("%Y-%m-%d") 
    
    professionals = db.session.query(Professional).all()
    
    professionals_data = [
        {"name": p.expertise, "rating": p.rating}
        for p in professionals
    ]

    rendered_html = render_template('monthly_report.html',
                                    flagged_customers_count=flagged_customers_count,
                                    total_customers_count=total_customers_count,
                                    flagged_professionals_count=flagged_professionals_count,
                                    total_professionals_count=total_professionals_count,
                                    pending_requests=pending_requests,
                                    completed_requests=completed_requests,
                                    rejected_requests=rejected_requests,
                                    professionals_data=professionals_data,
                                    current_date=current_date)

    pdf = pdfkit.from_string(rendered_html, False)

    response = Response(pdf, content_type='application/pdf')
    response.headers['Content-Disposition'] = 'attachment; filename=monthly_report.pdf'
    return response


from app import db
from ...users.models import User

class Customer(db.Model):
    __tablename__ = "Customer"
    customer_id = db.Column(db.Integer, primary_key=True)
    flagged = db.Column(db.String(5), default="False")
    address = db.Column(db.String(200), nullable=False)  
    phone_number = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id"), nullable=False)
    rating = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", back_populates="customer", uselist=False)
    service_requests = db.relationship("ServiceRequest", back_populates="customer", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "flagged": self.flagged,
            "address": self.address,
            "phone_number": self.phone_number,
            "user_id": self.user_id,
            "rating": self.rating,
            "user": {
                "username": self.user.username,
                "email": self.user.email,
                "role": self.user.role,
            } if self.user else None,
            "service_requests": [request.to_dict_basic() for request in self.service_requests],  # Use basic method here
        }

class ServiceRequest(db.Model):
    __tablename__ = "ServiceRequest"
    request_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")  
    request_date = db.Column(db.DateTime, nullable=False)
    service_date = db.Column(db.DateTime, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    otp = db.Column(db.String(6), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey("Service.service_id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("Customer.customer_id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("Professional.professional_id"), nullable=False)

    customer = db.relationship("Customer", back_populates="service_requests")
    professional = db.relationship("Professional", back_populates="service_requests")
    service = db.relationship("Service", back_populates="service_requests")

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "status": self.status,
            "request_date": self.request_date.isoformat() if self.request_date else None,
            "service_date": self.service_date.isoformat() if self.service_date else None,
            "rating": self.rating,
            "otp": self.otp,
            "service_id": self.service_id,
            "customer_id": self.customer_id,
            "professional_id": self.professional_id,
            "customer": self.customer.to_dict() if self.customer else None,
           "customer": {
            "username": self.customer.user.username if self.customer and self.customer.user else None,
            "email": self.customer.user.email if self.customer and self.customer.user else None,
            "role": self.customer.user.role if self.customer and self.customer.user else None,
            "address":self.customer.address,
            "phone_number":self.customer.phone_number
        },
            "professional": {
                "username": self.professional.user.username if self.professional and self.professional.user else None,
                "role": self.professional.user.role if self.professional and self.professional.user else None,
            } if self.professional else None,
            "service": {
                "name": self.service.name,
                "description": self.service.description,
                "base_price": self.service.base_price,
            } if self.service else None,
        }

    def to_dict_basic(self):
        """ Helper function to avoid recursion issues. """
        return {
            "request_id": self.request_id,
            "status": self.status,
            "request_date": self.request_date.isoformat() if self.request_date else None,
            "service_date": self.service_date.isoformat() if self.service_date else None,
            "rating": self.rating,
            "otp": self.otp,
            "service_id": self.service_id,
            "customer_id": self.customer_id,
            "professional_id": self.professional_id,
        }
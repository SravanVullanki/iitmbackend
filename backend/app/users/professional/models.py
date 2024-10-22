from app import db
from ...users.models import User

class Professional(db.Model):
    __tablename__ = "Professional"
    
    professional_id = db.Column(db.Integer, primary_key=True)
    expertise = db.Column(db.String(100), nullable=False)  
    experience_years = db.Column(db.Integer, nullable=False)  
    pdf_resume = db.Column(db.LargeBinary, nullable=False)  
    status = db.Column(db.String(10), default="Pending")  
    rating = db.Column(db.Float(10, 2), default=0)  
    rating_count = db.Column(db.Integer, default=0)
    flagged = db.Column(db.String(5), default="False")  

    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id"), nullable=False)
    user = db.relationship("User", back_populates="professional", uselist=False)
    
    services_offered = db.relationship("Service", back_populates="professional", cascade="all, delete-orphan")
    service_requests = db.relationship("ServiceRequest", back_populates="professional", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "professional_id": self.professional_id,
            "expertise": self.expertise,
            "experience_years": self.experience_years,
            "status": self.status,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "flagged": self.flagged,
            "user_id": self.user_id,
            "user": {
                "username": self.user.username,
                "role": self.user.role,
            } if self.user else None,
            "services_offered": [service.to_dict_basic() for service in self.services_offered],  
            "service_requests": [request.to_dict_basic() for request in self.service_requests],  # Avoid full dict for requests
        }

    def to_dict_basic(self):
        """ Helper function to avoid recursion issues. """
        return {
            "professional_id": self.professional_id,
            "expertise": self.expertise,
            "experience_years": self.experience_years,
            "status": self.status,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "flagged": self.flagged,
            "user_id": self.user_id,
        }

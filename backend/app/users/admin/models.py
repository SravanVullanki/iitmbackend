from app import db

class Admin(db.Model):
    __tablename__ = "Admin"
    admin_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id"), nullable=False)
    user = db.relationship("User", back_populates="admin", uselist=False)

    def to_dict(self):
        return {
            "admin_id": self.admin_id,
            "user_id": self.user_id,
            "user": {
                "username": self.user.username,
                "role": self.user.role,
            } if self.user else None,
        }

class Service(db.Model):
    __tablename__ = "Service"
    service_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    base_price = db.Column(db.Float(10, 2), nullable=False) 
    professional_id = db.Column(db.Integer, db.ForeignKey("Professional.professional_id"), nullable=False)
    
    professional = db.relationship("Professional", back_populates="services_offered")
    service_requests = db.relationship("ServiceRequest", back_populates="service")

    def to_dict(self):
        """Returns the full service details including the associated professional."""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "description": self.description,
            "base_price": self.base_price,
            "professional_id": self.professional_id,
            "professional": {
                "professional_id": self.professional.professional_id,
                "username": self.professional.user.username if self.professional and self.professional.user else None,
                "role": self.professional.user.role if self.professional and self.professional.user else None,
                "rating":self.professional.rating
            } if self.professional else None,
            "service_requests": [request.to_dict_basic() for request in self.service_requests],  # Include service requests details
        }

    def to_dict_basic(self):
        """Returns a simplified representation of the service."""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "base_price": self.base_price,
        }

    def to_dict_with_professional(self):
        """Returns service info with professional details while avoiding recursion issues."""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "description": self.description,
            "base_price": self.base_price,
            "professional": {
                "professional_id": self.professional.professional_id,
                "username": self.professional.user.username if self.professional and self.professional.user else None,
                "role": self.professional.user.role if self.professional and self.professional.user else None,
            } if self.professional else None,
        }

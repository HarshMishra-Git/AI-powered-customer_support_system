from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """Model for user accounts"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'admin' or 'customer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # User preferences
    theme_preference = db.Column(db.String(20), nullable=False, default='light')  # 'dark' or 'light'
    # Gamification
    experience_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    badges_earned = db.Column(db.String(1000), default='[]')  # JSON string of earned badges
    # Relationship with tickets
    tickets = db.relationship('Ticket', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Set the password hash from a plain text password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'theme_preference': self.theme_preference,
            'experience_points': self.experience_points,
            'level': self.level,
            'badges_earned': self.badges_earned
        }

class Ticket(db.Model):
    """Model for support tickets"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    issue_category = db.Column(db.String(100), nullable=False)
    sentiment = db.Column(db.String(50))
    priority = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default="Open")
    resolution = db.Column(db.Text)
    resolution_status = db.Column(db.String(20), default="Pending")
    resolution_date = db.Column(db.DateTime)
    # New fields for enhanced functionality
    assigned_to = db.Column(db.String(50))  # For team assignment
    summary = db.Column(db.Text)  # For automated summary
    extracted_actions = db.Column(db.Text)  # For action extraction
    estimated_resolution_time = db.Column(db.Float)  # In hours
    team_id = db.Column(db.String(50))  # For team assignment
    # User relationship
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'issue_category': self.issue_category,
            'sentiment': self.sentiment,
            'priority': self.priority,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'resolution': self.resolution,
            'resolution_status': self.resolution_status,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'assigned_to': self.assigned_to,
            'summary': self.summary,
            'extracted_actions': self.extracted_actions,
            'estimated_resolution_time': self.estimated_resolution_time,
            'team_id': self.team_id
        }

class Conversation(db.Model):
    """Model for conversations related to tickets"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), db.ForeignKey('ticket.ticket_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'agent', 'system'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'message': self.message,
            'sender': self.sender,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Solution(db.Model):
    """Model for pre-defined solutions based on historical data"""
    id = db.Column(db.Integer, primary_key=True)
    issue_category = db.Column(db.String(100), nullable=False)
    solution_text = db.Column(db.Text, nullable=False)
    success_rate = db.Column(db.Float, default=0.0)
    usage_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'issue_category': self.issue_category,
            'solution_text': self.solution_text,
            'success_rate': self.success_rate,
            'usage_count': self.usage_count
        }

class Feedback(db.Model):
    """Model for customer feedback on ticket resolutions"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), db.ForeignKey('ticket.ticket_id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 scale
    comment = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'rating': self.rating,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Team(db.Model):
    """Model for different support teams"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    specialization = db.Column(db.String(100))  # What type of issues this team handles
    current_workload = db.Column(db.Integer, default=0)  # Number of active tickets

    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'specialization': self.specialization,
            'current_workload': self.current_workload
        }

class TeamMember(db.Model):
    """Model for individual team members"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.String(50), db.ForeignKey('team.team_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    expertise = db.Column(db.String(100))  # Specific area of expertise
    availability = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'expertise': self.expertise,
            'availability': self.availability
        }

class TicketMetrics(db.Model):
    """Model for storing ticket resolution metrics"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), db.ForeignKey('ticket.ticket_id'), nullable=False)
    time_to_first_response = db.Column(db.Float)  # In minutes
    resolution_time = db.Column(db.Float)  # In hours
    reopened_count = db.Column(db.Integer, default=0)
    message_count = db.Column(db.Integer, default=0)
    user_message_count = db.Column(db.Integer, default=0)
    agent_message_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'time_to_first_response': self.time_to_first_response,
            'resolution_time': self.resolution_time,
            'reopened_count': self.reopened_count,
            'message_count': self.message_count,
            'user_message_count': self.user_message_count,
            'agent_message_count': self.agent_message_count
        }

class Badge(db.Model):
    """Model for gamification badges"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(255))  # Icon path or class
    criteria = db.Column(db.Text, nullable=False)  # JSON string describing how to earn the badge
    category = db.Column(db.String(50))  # Category of badge (e.g., 'Speed', 'Quality', 'Quantity')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'criteria': self.criteria,
            'category': self.category
        }

class KnowledgeBaseEntry(db.Model):
    """Model for knowledge base entries that grow with resolved tickets"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text)  # JSON string of tags
    source_ticket_id = db.Column(db.String(20), db.ForeignKey('ticket.ticket_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    views_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'source_ticket_id': self.source_ticket_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'views_count': self.views_count,
            'helpful_count': self.helpful_count
        }

class EmojiReaction(db.Model):
    """Model for emoji reactions on tickets and messages"""
    id = db.Column(db.Integer, primary_key=True)
    emoji_code = db.Column(db.String(50), nullable=False)  # Unicode or shortcode for emoji
    target_type = db.Column(db.String(20), nullable=False)  # 'ticket' or 'message'
    target_id = db.Column(db.Integer, nullable=False)  # ID of the ticket or message
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'emoji_code': self.emoji_code,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CollaborationSession(db.Model):
    """Model for real-time collaboration sessions"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), db.ForeignKey('ticket.ticket_id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    session_notes = db.Column(db.Text)  # Collaboration notes
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'session_notes': self.session_notes,
            'is_active': self.is_active
        }

class CollaborationParticipant(db.Model):
    """Model for participants in collaboration sessions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('collaboration_session.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'is_active': self.is_active
        }
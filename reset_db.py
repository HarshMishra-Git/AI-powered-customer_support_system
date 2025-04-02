
import os
import logging
from app import app, db
from models import Ticket, Conversation, Solution, Feedback, Team, TeamMember, TicketMetrics, User
from data_processing import load_initial_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_default_users():
    """Initialize default admin and customer users"""
    try:
        # Create default admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        admin.set_password("admin123")
        
        # Create default customer user
        customer = User(
            username="customer",
            email="customer@example.com",
            role="customer"
        )
        customer.set_password("customer123")
        
        db.session.add(admin)
        db.session.add(customer)
        db.session.commit()
        
        logger.info("Added default admin and customer users")
    except Exception as e:
        logger.error(f"Error creating default users: {str(e)}")
        db.session.rollback()

def init_default_teams():
    """Initialize default teams in the database"""
    teams = [
        {
            "team_id": "TECH_SUPPORT",
            "name": "Technical Support",
            "description": "Front-line support for technical issues",
            "specialization": "General Technical Support"
        },
        {
            "team_id": "NETWORK",
            "name": "Network Team",
            "description": "Specialized support for network connectivity issues",
            "specialization": "Network Connectivity Issues" 
        },
        {
            "team_id": "SOFTWARE",
            "name": "Software Team",
            "description": "Specialized support for software installation and bugs",
            "specialization": "Software Installation Issues"
        },
        {
            "team_id": "ACCOUNT",
            "name": "Account Management",
            "description": "Specialized support for account-related issues",
            "specialization": "Account Synchronization Issues"
        },
        {
            "team_id": "PAYMENT",
            "name": "Payment Gateway Team",
            "description": "Specialized support for payment-related issues",
            "specialization": "Payment Gateway Issues"
        }
    ]
    
    # Add team members (sample data)
    team_members = [
        {
            "team_id": "TECH_SUPPORT",
            "name": "John Smith",
            "email": "john.smith@example.com",
            "role": "Team Lead",
            "expertise": "General Troubleshooting"
        },
        {
            "team_id": "NETWORK",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com",
            "role": "Senior Network Engineer",
            "expertise": "Network Security"
        },
        {
            "team_id": "SOFTWARE",
            "name": "Michael Brown",
            "email": "michael.brown@example.com",
            "role": "Software Specialist",
            "expertise": "Installation Issues"
        },
        {
            "team_id": "ACCOUNT",
            "name": "Emily Davis",
            "email": "emily.davis@example.com",
            "role": "Account Specialist",
            "expertise": "Account Recovery"
        },
        {
            "team_id": "PAYMENT",
            "name": "David Wilson",
            "email": "david.wilson@example.com",
            "role": "Payment Systems Engineer",
            "expertise": "Transaction Processing"
        }
    ]
    
    try:
        # Add teams
        for team_data in teams:
            team = Team(**team_data)
            db.session.add(team)
        
        db.session.commit()
        logger.info(f"Added {len(teams)} default teams")
        
        # Add team members
        for member_data in team_members:
            member = TeamMember(**member_data)
            db.session.add(member)
        
        db.session.commit()
        logger.info(f"Added {len(team_members)} default team members")
    except Exception as e:
        logger.error(f"Error initializing default teams: {str(e)}")
        db.session.rollback()

def reset_database():
    logger.info("Dropping all tables...")
    db.drop_all()
    logger.info("Creating all tables...")
    db.create_all()
    logger.info("Database reset complete!")

if __name__ == "__main__":
    with app.app_context():
        reset_database()
        logger.info("Initializing default teams...")
        init_default_teams()
        logger.info("Creating default users...")
        init_default_users()
        logger.info("Loading initial data...")
        load_initial_data()
        logger.info("Database reset complete!")

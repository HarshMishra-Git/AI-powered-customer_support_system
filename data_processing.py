import logging
import csv
import os
import re
import random
from datetime import datetime, timedelta
from app import db
from models import Ticket, Solution, Conversation, TicketMetrics # Fixed model import name

logger = logging.getLogger(__name__)

def load_initial_data():
    """Load initial ticket data from CSV and conversation data from TXT files"""
    try:
        # Check if data already exists
        if db.session.query(Ticket).count() > 0:
            logger.info("Database already contains tickets, skipping initial data load")
            return

        # Load historical ticket data from CSV
        load_historical_tickets()

        # Load conversation data from TXT files
        load_conversation_data()

        logger.info("Initial data loading completed successfully")
    except Exception as e:
        logger.error(f"Error loading initial data: {str(e)}")

def load_historical_tickets():
    """Load historical ticket data from the CSV file"""
    try:
        csv_path = os.path.join('attached_assets', 'Historical_ticket_data.csv')

        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found at {csv_path}")
            return

        with open(csv_path, 'r') as file:
            csv_content = file.read()
            # Remove BOM if present
            if csv_content.startswith('\ufeff'):
                csv_content = csv_content.replace('\ufeff', '')

            # Remove spaces in column names
            header_line = csv_content.splitlines()[0]
            clean_header = header_line.replace(' ', '')

            # Replace first line with clean header
            csv_content = clean_header + '\n' + '\n'.join(csv_content.splitlines()[1:])

            # Use clean CSV content
            reader = csv.DictReader(csv_content.splitlines())

            for row in reader:
                ticket_id = row.get('TicketID') or row.get('Ticket_ID') or row.get('TicketId')
                if not ticket_id:  # Skip if no ticket ID found
                    continue

                issue_category = row.get('IssueCategory') or row.get('Issue_Category')
                sentiment = row.get('Sentiment')
                priority = row.get('Priority')
                solution = row.get('Solution')
                resolution_status = row.get('ResolutionStatus') or row.get('Resolution_Status')
                date_of_resolution = row.get('DateofResolution') or row.get('Date_of_Resolution')
                creation_date = row.get('CreationDate') # Assuming creation date is available

                # Create ticket entry with safe null checks
                ticket = Ticket(
                    ticket_id=ticket_id.strip() if ticket_id else f"TECH_{random.randint(100, 999)}",
                    issue_category=issue_category.strip() if issue_category else "General Issue",
                    sentiment=sentiment.strip() if sentiment else "Neutral",
                    priority=priority.strip() if priority else "Medium",
                    description=f"Historical ticket: {issue_category.strip() if issue_category else 'General Issue'}",  # We don't have actual descriptions
                    status="Closed",
                    resolution=solution.strip() if solution else "No solution provided",
                    resolution_status=resolution_status.strip() if resolution_status else "Resolved",
                    resolution_date=datetime.strptime(date_of_resolution.strip(), '%Y-%m-%d') if date_of_resolution else None,
                    creation_date = datetime.strptime(creation_date.strip(), '%Y-%m-%d') if creation_date else None # Added creation date
                )

                db.session.add(ticket)

                # Calculate resolution hours (assuming creation_date exists)
                resolution_hours = None
                if ticket.resolution_date and ticket.creation_date:
                    resolution_hours = (ticket.resolution_date - ticket.creation_date).total_seconds() / 3600

                #Adding metrics to the database.
                metrics = TicketMetrics(
                    ticket_id=ticket.ticket_id,
                    resolution_hours=resolution_hours,
                    success_rate=1.0 if resolution_status == "Resolved" else 0.0 #Assuming resolved means success
                )
                db.session.add(metrics)


                # Skip adding solution if it's null or empty
                if not solution:
                    continue

                # Also add the solution to our solutions table
                safe_issue_category = issue_category.strip() if issue_category else "General Issue"
                safe_solution_text = solution.strip() if solution else "No solution provided"

                existing_solution = db.session.query(Solution).filter_by(
                    issue_category=safe_issue_category,
                    solution_text=safe_solution_text
                ).first()

                if not existing_solution:
                    new_solution = Solution(
                        issue_category=safe_issue_category,
                        solution_text=safe_solution_text,
                        success_rate=0.8,  # Assuming resolved tickets had successful solutions
                        usage_count=1
                    )
                    db.session.add(new_solution)
                else:
                    existing_solution.usage_count += 1

            db.session.commit()
            logger.info(f"Loaded historical ticket data from {csv_path}")
    except Exception as e:
        logger.error(f"Error loading historical tickets: {str(e)}")
        db.session.rollback()

def load_conversation_data():
    """Load conversation data from TXT files"""
    try:
        conversation_files = [
            "Account Synchronization Bug.txt",
            "Device Compatibility Error.txt",
            "Network Connectivity Issue.txt",
            "Payment Gateway Integration Failure.txt",
            "Software Installation Failure.txt"
        ]

        for filename in conversation_files:
            file_path = os.path.join('attached_assets', filename)

            if not os.path.exists(file_path):
                logger.warning(f"Conversation file not found: {file_path}")
                continue

            with open(file_path, 'r') as file:
                lines = file.readlines()

                # Extract ticket ID from first line
                ticket_id_match = re.search(r'TECH_\d+', lines[0])
                if not ticket_id_match:
                    logger.warning(f"Could not extract ticket ID from {filename}")
                    continue

                ticket_id = ticket_id_match.group(0)

                # Extract category from second line
                category_match = re.search(r'Category: (.+)', lines[1])
                category = category_match.group(1) if category_match else "General Issue"

                # Extract sentiment and priority from third line
                sentiment_priority_match = re.search(r'Sentiment: (\w+) \| Priority: (\w+)', lines[2])
                sentiment = sentiment_priority_match.group(1) if sentiment_priority_match else "Neutral"
                priority = sentiment_priority_match.group(2) if sentiment_priority_match else "Medium"

                # Create the ticket if it doesn't exist
                ticket = db.session.query(Ticket).filter_by(ticket_id=ticket_id).first()
                if not ticket:
                    # Extract customer's issue from the fourth line
                    customer_issue_match = re.search(r'Customer: "(.+)"', lines[3])
                    customer_issue = customer_issue_match.group(1) if customer_issue_match else "Unknown issue"

                    ticket = Ticket(
                        ticket_id=ticket_id,
                        issue_category=category,
                        sentiment=sentiment,
                        priority=priority,
                        description=customer_issue,
                        status="Closed",
                        resolution_status="Resolved",
                        resolution_date=datetime.utcnow()
                    )
                    db.session.add(ticket)

                # Process conversation messages
                for i in range(3, len(lines)):
                    line = lines[i]

                    customer_match = re.search(r'Customer: "(.+)"', line)
                    agent_match = re.search(r'Agent: "(.+)"', line)

                    if customer_match:
                        message = customer_match.group(1)
                        conversation = Conversation(
                            ticket_id=ticket_id,
                            message=message,
                            sender="user"
                        )
                        db.session.add(conversation)

                    if agent_match:
                        message = agent_match.group(1)
                        conversation = Conversation(
                            ticket_id=ticket_id,
                            message=message,
                            sender="agent"
                        )
                        db.session.add(conversation)

                        # Use the last agent message as the resolution
                        ticket.resolution = message

            db.session.commit()
            logger.info(f"Loaded conversation data from {filename}")
    except Exception as e:
        logger.error(f"Error loading conversation data: {str(e)}")
        db.session.rollback()
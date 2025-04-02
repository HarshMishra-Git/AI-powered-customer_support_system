import logging
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import Ticket, Conversation, Solution, Feedback, Team, TeamMember, TicketMetrics, User, Badge, KnowledgeBaseEntry, EmojiReaction, CollaborationSession, CollaborationParticipant
from agents import ClassifierAgent, ResolutionAgent, EscalationAgent, FeedbackAgent, ChatbotAgent
from data_processing import load_initial_data
from forms import LoginForm, RegistrationForm, ProfileUpdateForm, UserPreferencesForm
from datetime import datetime
import uuid
import random
import utils

logger = logging.getLogger(__name__)

# Initialize agent references
classifier_agent = None
resolution_agent = None
escalation_agent = None
feedback_agent = None
chatbot_agent = None

def initialize_agents():
    """Initialize all agents - called within app context"""
    global classifier_agent, resolution_agent, escalation_agent, feedback_agent, chatbot_agent
    
    logger.info("Initializing agents...")
    classifier_agent = ClassifierAgent()
    resolution_agent = ResolutionAgent()
    escalation_agent = EscalationAgent()
    feedback_agent = FeedbackAgent()
    chatbot_agent = ChatbotAgent()
    logger.info("Agents initialized successfully")

def register_routes(app):
    """Register all routes with the Flask app"""
    
    # Set up data loading and initialize agents
    with app.app_context():
        load_initial_data()
        initialize_agents()
        
    @app.route('/load-initial-data')
    def load_initial_data_route():
        """Route to manually trigger data loading if needed"""
        load_initial_data()
        return "Initial data loaded successfully"
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route"""
        # If user is already logged in, redirect to home page
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = LoginForm()
        if form.validate_on_submit():
            # Look up user by username
            user = User.query.filter_by(username=form.username.data).first()
            
            # Check if user exists and password is correct
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'danger')
                return redirect(url_for('login'))
                
            # Log in user
            login_user(user, remember=form.remember_me.data)
            flash('Login successful!', 'success')
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
            
        return render_template('auth/login.html', form=form)
        
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Register new user route"""
        # If user is already logged in, redirect to home page
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = RegistrationForm()
        if form.validate_on_submit():
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='customer'  # Default role is customer
            )
            user.set_password(form.password.data)
            
            # Save user to database
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('auth/register.html', form=form)
        
    @app.route('/logout')
    def logout():
        """Logout route"""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
        
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """User profile management"""
        profile_form = ProfileUpdateForm(original_username=current_user.username, original_email=current_user.email)
        pref_form = UserPreferencesForm()
        
        # Handle profile update form submission
        if profile_form.validate_on_submit() and 'update_profile' in request.form:
            # Verify current password
            if not current_user.check_password(profile_form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))
                
            # Update user data
            current_user.username = profile_form.username.data
            current_user.email = profile_form.email.data
            
            # Update password if provided
            if profile_form.new_password.data:
                current_user.set_password(profile_form.new_password.data)
                
            db.session.commit()
            flash('Your profile has been updated.', 'success')
            return redirect(url_for('profile'))
            
        # Handle preferences form submission
        elif pref_form.validate_on_submit() and 'save_preferences' in request.form:
            current_user.theme_preference = pref_form.theme_preference.data
            db.session.commit()
            flash('Your preferences have been saved.', 'success')
            return redirect(url_for('profile'))
            
        elif request.method == 'GET':
            # Pre-populate forms with current user data
            profile_form.username.data = current_user.username
            profile_form.email.data = current_user.email
            pref_form.theme_preference.data = current_user.theme_preference
            
        return render_template('auth/profile.html', profile_form=profile_form, pref_form=pref_form)

    @app.route('/')
    def index():
        """Render the main page"""
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Render the dashboard page"""
        # Only admins can access the dashboard
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return render_template('dashboard.html')
    
    @app.route('/tickets')
    @login_required
    def tickets():
        """Render the tickets page"""
        return render_template('tickets.html')
    
    @app.route('/chat')
    def chat():
        """Render the chat page"""
        return render_template('chat.html')
        
    @app.route('/knowledge-base')
    def knowledge_base():
        """Render the knowledge base page"""
        return render_template('knowledge_base.html')
    
    @app.route('/api/tickets', methods=['GET'])
    @login_required
    def get_tickets():
        """API endpoint to get all tickets"""
        try:
            ticket_status = request.args.get('status', None)
            
            # Filter tickets based on user role
            if current_user.is_admin():
                # Admins can see all tickets
                if ticket_status:
                    tickets = Ticket.query.filter_by(status=ticket_status).order_by(Ticket.created_at.desc()).all()
                else:
                    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
            else:
                # Regular users can only see their own tickets
                if ticket_status:
                    tickets = Ticket.query.filter_by(status=ticket_status, user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
                else:
                    tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
            
            return jsonify({
                'success': True,
                'tickets': [ticket.to_dict() for ticket in tickets]
            })
        except Exception as e:
            logger.error(f"Error getting tickets: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve tickets'
            }), 500
    
    @app.route('/api/tickets/<ticket_id>', methods=['GET'])
    @login_required
    def get_ticket(ticket_id):
        """API endpoint to get a specific ticket with its conversation history"""
        try:
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Check permissions: only admin or ticket owner can view the ticket
            if not current_user.is_admin() and ticket.user_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'You do not have permission to view this ticket'
                }), 403
            
            # Get conversation history
            conversations = Conversation.query.filter_by(ticket_id=ticket_id).order_by(Conversation.timestamp).all()
            
            return jsonify({
                'success': True,
                'ticket': ticket.to_dict(),
                'conversations': [conv.to_dict() for conv in conversations]
            })
        except Exception as e:
            logger.error(f"Error getting ticket {ticket_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve ticket'
            }), 500
    
    @app.route('/api/tickets', methods=['POST'])
    @login_required
    def create_ticket():
        """API endpoint to create a new ticket"""
        try:
            data = request.get_json()
            
            if not data or 'description' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Description is required'
                }), 400
            
            # Classify the ticket
            classification = classifier_agent.classify_ticket(data['description'])
            
            # Generate ticket ID in TECH_XXX format to match the dataset
            next_id = random.randint(100, 999)
            ticket_id = f"TECH_{next_id}"
            
            # Create the ticket with enhanced data and associate with current user
            new_ticket = Ticket(
                ticket_id=ticket_id,
                issue_category=classification["issue_category"],
                sentiment=classification["sentiment"],
                priority=classification["priority"],
                description=data['description'],
                status="Open",
                resolution_status="Pending",
                summary=classification.get("summary", ""),
                extracted_actions=classification.get("extracted_actions", ""),
                estimated_resolution_time=classification.get("estimated_resolution_time", 2.0),
                team_id=classification.get("team_id", "TECH_SUPPORT"),
                user_id=current_user.id
            )
            
            db.session.add(new_ticket)
            db.session.commit()
            
            # Add the initial message if provided
            if 'initial_message' in data:
                conversation = Conversation(
                    ticket_id=ticket_id,
                    message=data['initial_message'],
                    sender="user"
                )
                
                db.session.add(conversation)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'ticket': new_ticket.to_dict()
            })
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to create ticket'
            }), 500
    
    @app.route('/api/tickets/<ticket_id>', methods=['PUT'])
    def update_ticket(ticket_id):
        """API endpoint to update a ticket"""
        try:
            data = request.get_json()
            
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Update ticket fields
            if 'status' in data:
                ticket.status = data['status']
            
            if 'resolution_status' in data:
                ticket.resolution_status = data['resolution_status']
            
            if 'resolution' in data:
                ticket.resolution = data['resolution']
                if data['resolution_status'] == 'Resolved':
                    ticket.resolution_date = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'ticket': ticket.to_dict()
            })
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id}: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to update ticket'
            }), 500
    
    @app.route('/api/tickets/<ticket_id>/conversation', methods=['POST'])
    def add_conversation(ticket_id):
        """API endpoint to add a message to a ticket conversation"""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data or 'sender' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Message and sender are required'
                }), 400
            
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Add the message to the conversation
            new_message = Conversation(
                ticket_id=ticket_id,
                message=data['message'],
                sender=data['sender']
            )
            
            db.session.add(new_message)
            db.session.commit()
            
            # Check if we need to respond automatically
            if data['sender'] == 'user' and ticket.status == 'Open':
                # Get conversation history
                conversations = Conversation.query.filter_by(ticket_id=ticket_id).order_by(Conversation.timestamp).all()
                conversation_history = [conv.to_dict() for conv in conversations]
                
                # Check if we should escalate
                should_escalate, reason = escalation_agent.should_escalate(ticket, conversation_history)
                
                if should_escalate:
                    # Add a system message indicating escalation
                    escalation_message = Conversation(
                        ticket_id=ticket_id,
                        message=f"This ticket has been escalated for human review. Reason: {reason}",
                        sender="system"
                    )
                    
                    db.session.add(escalation_message)
                    
                    # Update ticket status
                    ticket.status = "Escalated"
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'conversation': new_message.to_dict(),
                        'escalated': True,
                        'reason': reason
                    })
                else:
                    # Get resolution suggestions
                    solutions = resolution_agent.suggest_solutions(ticket)
                    
                    if solutions:
                        # Use the first solution as a response
                        solution_text = solutions[0]['solution_text']
                        
                        # Add the solution as an agent message
                        agent_message = Conversation(
                            ticket_id=ticket_id,
                            message=solution_text,
                            sender="agent"
                        )
                        
                        db.session.add(agent_message)
                        db.session.commit()
                        
                        return jsonify({
                            'success': True,
                            'conversation': new_message.to_dict(),
                            'agent_response': agent_message.to_dict(),
                            'solutions': solutions
                        })
            
            return jsonify({
                'success': True,
                'conversation': new_message.to_dict()
            })
        except Exception as e:
            logger.error(f"Error adding conversation to ticket {ticket_id}: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to add conversation'
            }), 500
    
    @app.route('/api/tickets/<ticket_id>/suggest-solutions', methods=['GET'])
    def suggest_solutions(ticket_id):
        """API endpoint to get solution suggestions for a ticket"""
        try:
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # First check knowledge base for relevant entries
            kb_entries = utils.find_knowledge_base_entries_for_issue(
                ticket.description, 
                category=ticket.issue_category,
                limit=2
            )
            
            # Format knowledge base entries as solutions
            kb_solutions = []
            for entry in kb_entries:
                kb_solutions.append({
                    'solution_text': f"Based on our knowledge base: {entry.title}\n\n{entry.content[:300]}...\n\nYou can view the full solution in our knowledge base.",
                    'success_rate': 0.9,  # Assume high success rate for KB entries
                    'source': 'knowledge_base',
                    'kb_entry_id': entry.id
                })
            
            # Get solutions from the resolution agent
            agent_solutions = resolution_agent.suggest_solutions(ticket)
            
            # Combine solutions, prioritizing knowledge base entries
            solutions = kb_solutions + agent_solutions
            
            return jsonify({
                'success': True,
                'solutions': solutions,
                'kb_entries': [entry.to_dict() for entry in kb_entries]
            })
        except Exception as e:
            logger.error(f"Error suggesting solutions for ticket {ticket_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to suggest solutions'
            }), 500
            
    @app.route('/api/tickets/<ticket_id>/knowledge-base', methods=['GET'])
    def get_related_knowledge_entries(ticket_id):
        """API endpoint to get knowledge base entries related to a ticket"""
        try:
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Find related knowledge base entries
            kb_entries = utils.find_knowledge_base_entries_for_issue(
                ticket.description, 
                category=ticket.issue_category,
                limit=5
            )
            
            return jsonify({
                'success': True,
                'ticket': ticket.to_dict(),
                'related_kb_entries': [entry.to_dict() for entry in kb_entries]
            })
        except Exception as e:
            logger.error(f"Error finding related KB entries for ticket {ticket_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to find related knowledge base entries'
            }), 500
    
    @app.route('/api/tickets/<ticket_id>/feedback', methods=['POST'])
    def add_feedback(ticket_id):
        """API endpoint to add feedback for a ticket"""
        try:
            data = request.get_json()
            
            if not data or 'rating' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Rating is required'
                }), 400
            
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Create feedback
            feedback = Feedback(
                ticket_id=ticket_id,
                rating=data['rating'],
                comment=data.get('comment', '')
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            # Process feedback to update solution success rates
            feedback_agent.process_feedback(ticket_id, data['rating'], data.get('comment', ''))
            
            # If this is positive feedback (rating ≥ 4) and the ticket is resolved,
            # create a knowledge base entry from this ticket
            kb_entry = None
            if ticket.resolution_status == 'Resolved' and data['rating'] >= 4:
                # Use current user's ID or admin ID if available
                admin_id = current_user.id if current_user.is_authenticated else 1
                kb_entry = utils.create_knowledge_base_entry_from_ticket(ticket_id, admin_id)
                if kb_entry:
                    logger.info(f"Created knowledge base entry {kb_entry.id} from ticket {ticket_id}")
            
            return jsonify({
                'success': True,
                'feedback': feedback.to_dict(),
                'knowledge_base_entry_created': kb_entry is not None
            })
        except Exception as e:
            logger.error(f"Error adding feedback for ticket {ticket_id}: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to add feedback'
            }), 500
    
    @app.route('/api/metrics/<ticket_id>', methods=['GET'])
    def get_ticket_metrics(ticket_id):
        """API endpoint to get metrics for a specific ticket"""
        try:
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Get or create metrics for this ticket
            metrics = TicketMetrics.query.filter_by(ticket_id=ticket_id).first()
            
            if not metrics:
                # Create new metrics record
                conversations = Conversation.query.filter_by(ticket_id=ticket_id).order_by(Conversation.timestamp).all()
                
                first_response_time = None
                if len(conversations) > 1:
                    # Find first agent response after a user message
                    for i in range(1, len(conversations)):
                        if conversations[i-1].sender == "user" and conversations[i].sender == "agent":
                            first_response_time = (conversations[i].timestamp - conversations[i-1].timestamp).total_seconds() / 60  # in minutes
                            break
                
                # Count messages by type
                user_messages = sum(1 for conv in conversations if conv.sender == "user")
                agent_messages = sum(1 for conv in conversations if conv.sender == "agent")
                
                # Create metrics object
                metrics = TicketMetrics(
                    ticket_id=ticket_id,
                    time_to_first_response=first_response_time,
                    resolution_time=None,  # Will be calculated if resolved
                    message_count=len(conversations),
                    user_message_count=user_messages,
                    agent_message_count=agent_messages
                )
                
                # Calculate resolution time if resolved
                if ticket.resolution_date and ticket.created_at:
                    resolution_time = (ticket.resolution_date - ticket.created_at).total_seconds() / 3600  # in hours
                    metrics.resolution_time = resolution_time
                
                db.session.add(metrics)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'metrics': metrics.to_dict()
            })
        except Exception as e:
            logger.error(f"Error getting metrics for ticket {ticket_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get ticket metrics'
            }), 500
            
    @app.route('/api/chat', methods=['POST'])
    def chat_message():
        """API endpoint to interact with the chatbot"""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Message is required'
                }), 400
            
            # Get conversation history if provided
            conversation_history = data.get('conversation_history', [])
            
            # Get session ID if provided, or generate one
            session_id = data.get('session_id', 'default')
            
            # Get response from chatbot with conversation state management
            response = chatbot_agent.respond_to_query(
                data['message'], 
                conversation_history, 
                session_id
            )
            
            # Return response with additional state information
            return jsonify({
                'success': True,
                'response': response['response'],
                'create_ticket': response.get('create_ticket', False),
                'ticket_id': response.get('ticket_id'),
                'current_state': response.get('current_state', 'unknown')
            })
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to process chat message'
            }), 500
    
    @app.route('/api/teams', methods=['GET'])
    def get_teams():
        """API endpoint to get all teams"""
        try:
            teams = Team.query.all()
            return jsonify({
                'success': True,
                'teams': [team.to_dict() for team in teams]
            })
        except Exception as e:
            logger.error(f"Error getting teams: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve teams'
            }), 500
    
    @app.route('/api/teams/<team_id>', methods=['GET'])
    def get_team(team_id):
        """API endpoint to get a specific team with its members"""
        try:
            team = Team.query.filter_by(team_id=team_id).first()
            
            if not team:
                return jsonify({
                    'success': False,
                    'message': 'Team not found'
                }), 404
            
            # Get team members
            members = TeamMember.query.filter_by(team_id=team_id).all()
            
            # Get active tickets for this team
            tickets = Ticket.query.filter_by(team_id=team_id, status='Open').all()
            
            return jsonify({
                'success': True,
                'team': team.to_dict(),
                'members': [member.to_dict() for member in members],
                'active_tickets': len(tickets)
            })
        except Exception as e:
            logger.error(f"Error getting team {team_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve team'
            }), 500
            
    @app.route('/api/tickets/<ticket_id>/assign-team', methods=['POST'])
    def assign_team(ticket_id):
        """API endpoint to assign a ticket to a team"""
        try:
            data = request.get_json()
            
            if not data or 'team_id' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Team ID is required'
                }), 400
            
            ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
            
            if not ticket:
                return jsonify({
                    'success': False,
                    'message': 'Ticket not found'
                }), 404
            
            # Check if team exists
            team = Team.query.filter_by(team_id=data['team_id']).first()
            if not team:
                return jsonify({
                    'success': False,
                    'message': 'Team not found'
                }), 404
            
            # Update ticket team
            ticket.team_id = data['team_id']
            
            # Also update assigned_to if provided
            if 'assigned_to' in data:
                ticket.assigned_to = data['assigned_to']
            
            # Update team workload
            team.current_workload = Ticket.query.filter_by(team_id=team.team_id, status='Open').count()
            
            db.session.commit()
            
            # Add a system message about the assignment
            assignment_message = Conversation(
                ticket_id=ticket_id,
                message=f"Ticket assigned to {team.name} team",
                sender="system"
            )
            
            db.session.add(assignment_message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'ticket': ticket.to_dict()
            })
        except Exception as e:
            logger.error(f"Error assigning team to ticket {ticket_id}: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to assign team'
            }), 500
    
    @app.route('/api/dashboard/stats', methods=['GET'])
    def dashboard_stats():
        """API endpoint to get dashboard statistics"""
        try:
            # Get ticket counts by status
            open_count = Ticket.query.filter_by(status='Open').count()
            closed_count = Ticket.query.filter_by(status='Closed').count()
            escalated_count = Ticket.query.filter_by(status='Escalated').count()
            
            # Get ticket counts by category
            categories = db.session.query(
                Ticket.issue_category,
                db.func.count(Ticket.id)
            ).group_by(Ticket.issue_category).all()
            
            category_counts = {category: count for category, count in categories}
            
            # Get average resolution time
            resolved_tickets = Ticket.query.filter(
                Ticket.resolution_date.isnot(None),
                Ticket.created_at.isnot(None)
            ).all()
            
            avg_resolution_time = 0
            if resolved_tickets:
                valid_tickets = []
                total_resolution_time = 0
                
                for ticket in resolved_tickets:
                    # Ensure resolution_date is after created_at for valid calculations
                    if ticket.resolution_date >= ticket.created_at:
                        time_diff = (ticket.resolution_date - ticket.created_at).total_seconds()
                        total_resolution_time += time_diff
                        valid_tickets.append(ticket)
                
                if valid_tickets:
                    avg_resolution_time = total_resolution_time / len(valid_tickets) / 3600  # in hours
                    # Ensure it's not negative and format to 2 decimal places
                    avg_resolution_time = abs(round(avg_resolution_time, 2))
            
            # Get solution success rates
            solutions = Solution.query.all()
            success_rates = {solution.issue_category: solution.success_rate for solution in solutions}
            
            # Get team workload statistics (new)
            teams = Team.query.all()
            team_stats = {}
            for team in teams:
                team_ticket_count = Ticket.query.filter_by(team_id=team.team_id, status='Open').count()
                team_stats[team.team_id] = {
                    'name': team.name,
                    'active_tickets': team_ticket_count,
                    'specialization': team.specialization
                }
            
            # Get average estimated resolution time vs actual resolution time (new)
            estimated_vs_actual = []
            for ticket in resolved_tickets:
                if ticket.estimated_resolution_time is not None and ticket.resolution_date >= ticket.created_at:
                    actual_time = (ticket.resolution_date - ticket.created_at).total_seconds() / 3600
                    # Make sure both values are positive
                    estimated_time = abs(ticket.estimated_resolution_time)
                    actual_time = abs(actual_time)
                    
                    estimated_vs_actual.append({
                        'ticket_id': ticket.ticket_id,
                        'estimated': round(estimated_time, 1),
                        'actual': round(actual_time, 1),
                        'category': ticket.issue_category
                    })
            
            # Get priority distribution (new)
            priority_counts = db.session.query(
                Ticket.priority,
                db.func.count(Ticket.id)
            ).group_by(Ticket.priority).all()
            
            priority_distribution = {priority: count for priority, count in priority_counts}
            
            return jsonify({
                'success': True,
                'ticket_counts': {
                    'open': open_count,
                    'closed': closed_count,
                    'escalated': escalated_count,
                    'total': open_count + closed_count + escalated_count
                },
                'category_counts': category_counts,
                'avg_resolution_time': round(avg_resolution_time, 2),
                'solution_success_rates': success_rates,
                'team_stats': team_stats,
                'estimated_vs_actual': estimated_vs_actual,
                'priority_distribution': priority_distribution
            })
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get dashboard statistics'
            }), 500
            
    @app.route('/api/knowledge-base', methods=['GET'])
    def get_knowledge_base():
        """API endpoint to get the knowledge base of resolved tickets"""
        try:
            # Get resolved tickets
            resolved_tickets = db.session.query(Ticket).filter(
                Ticket.status == "Resolved", 
                Ticket.resolution.isnot(None)
            ).all()
            
            # Organize by category
            knowledge_base = {}
            for ticket in resolved_tickets:
                if ticket.issue_category not in knowledge_base:
                    knowledge_base[ticket.issue_category] = []
                
                knowledge_base[ticket.issue_category].append({
                    "ticket_id": ticket.ticket_id,
                    "description": ticket.description,
                    "resolution": ticket.resolution,
                    "resolution_date": ticket.resolution_date.strftime("%Y-%m-%d %H:%M:%S") if ticket.resolution_date else None
                })
                
            return jsonify({
                "success": True,
                "knowledge_base": knowledge_base
            })
        except Exception as e:
            logger.error(f"Error fetching knowledge base: {str(e)}")
            return jsonify({"success": False, "message": "Error fetching knowledge base"})
            
    @app.route('/api/conversation-health', methods=['POST'])
    def analyze_conversation_health():
        """API endpoint to analyze conversation health"""
        try:
            data = request.get_json()
            
            if not data or 'ticket_id' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Ticket ID is required'
                }), 400
                
            ticket_id = data['ticket_id']
            
            # Get ticket conversations
            conversations = Conversation.query.filter_by(ticket_id=ticket_id).order_by(Conversation.timestamp).all()
            
            if not conversations:
                return jsonify({
                    'success': False,
                    'message': 'No conversations found for this ticket'
                }), 404
                
            # Convert to format expected by ConversationHealthAnalyzer
            conversation_history = []
            for convo in conversations:
                conversation_history.append({
                    "message": convo.message,
                    "sender": convo.sender,
                    "timestamp": convo.timestamp
                })
                
            # Create analyzer instance
            from ml_models import ConversationHealthAnalyzer
            health_analyzer = ConversationHealthAnalyzer()
            
            # Analyze conversation
            health_results = health_analyzer.analyze_conversation(conversation_history)
            
            return jsonify({
                'success': True,
                'health_score': health_results['health_score'],
                'metrics': health_results['metrics'],
                'suggestions': health_results['improvement_suggestions']
            })
            
        except Exception as e:
            logger.error(f"Error analyzing conversation health: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to analyze conversation health'
            }), 500
            
    @app.route('/api/collaboration/sessions', methods=['GET'])
    def get_collaboration_sessions():
        """API endpoint to get active collaboration sessions"""
        try:
            # In a real implementation, this would interact with the CollaborativeAgentSystem
            # For now, we'll create representative data based on active tickets
            
            # Get all teams
            teams = db.session.query(Team).all()
            team_map = {team.team_id: team.name for team in teams}
            
            # Get some active tickets
            active_tickets = db.session.query(Ticket).filter(
                Ticket.status.in_(["Open", "In Progress"])
            ).limit(5).all()
            
            sessions = []
            if active_tickets:
                import random
                from datetime import datetime, timedelta
                
                for i, ticket in enumerate(active_tickets):
                    # Create session data based on ticket info
                    agent_count = min(i + 1, 3)  # 1-3 agents per session
                    
                    # Calculate a reasonable start time (between ticket creation and now)
                    now = datetime.utcnow()
                    ticket_age = (now - ticket.created_at).total_seconds()
                    start_offset = random.uniform(0, ticket_age * 0.8)  # Start sometime after ticket creation
                    started_at = ticket.created_at + timedelta(seconds=start_offset)
                    
                    team_name = team_map.get(ticket.team_id, "Unassigned")
                    
                    sessions.append({
                        "ticket_id": ticket.ticket_id,
                        "issue_category": ticket.issue_category,
                        "priority": ticket.priority,
                        "active_agents": agent_count,
                        "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "team_id": ticket.team_id,
                        "team_name": team_name,
                        "message_count": random.randint(5, 20)
                    })
            
            return jsonify({
                "success": True,
                "sessions": sessions,
                "total_active_sessions": len(sessions)
            })
        except Exception as e:
            logger.error(f"Error fetching collaboration sessions: {str(e)}")
            return jsonify({"success": False, "message": "Error fetching collaboration sessions"})
            
    # User Preferences API
    @app.route('/api/theme-preference', methods=['GET', 'PUT'])
    @login_required
    def theme_preference():
        """API endpoint to get or update user theme preference"""
        try:
            if request.method == 'GET':
                return jsonify({
                    'success': True,
                    'theme_preference': current_user.theme_preference
                })
            else:  # PUT method
                data = request.get_json()
                if not data or 'theme_preference' not in data:
                    return jsonify({
                        'success': False,
                        'message': 'Theme preference is required'
                    }), 400
                    
                # Update user theme preference
                current_user.theme_preference = data['theme_preference']
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'theme_preference': current_user.theme_preference
                })
        except Exception as e:
            logger.error(f"Error handling theme preference: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to handle theme preference'
            }), 500
            
    # Emoji Reactions API
    @app.route('/api/emoji-reactions', methods=['POST'])
    @login_required
    def add_emoji_reaction():
        """API endpoint to add an emoji reaction"""
        try:
            data = request.get_json()
            
            if not data or 'emoji_code' not in data or 'target_type' not in data or 'target_id' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Emoji code, target type, and target ID are required'
                }), 400
                
            # Check if user already reacted with this emoji
            existing_reaction = EmojiReaction.query.filter_by(
                emoji_code=data['emoji_code'], 
                target_type=data['target_type'], 
                target_id=data['target_id'],
                user_id=current_user.id
            ).first()
            
            if existing_reaction:
                # Remove the reaction (toggle behavior)
                db.session.delete(existing_reaction)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'action': 'removed',
                    'reaction': existing_reaction.to_dict()
                })
            
            # Create new reaction
            new_reaction = EmojiReaction(
                emoji_code=data['emoji_code'],
                target_type=data['target_type'],
                target_id=data['target_id'],
                user_id=current_user.id
            )
            
            db.session.add(new_reaction)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'action': 'added',
                'reaction': new_reaction.to_dict()
            })
        except Exception as e:
            logger.error(f"Error adding emoji reaction: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to add emoji reaction'
            }), 500
            
    @app.route('/api/emoji-reactions/<target_type>/<int:target_id>', methods=['GET'])
    def get_emoji_reactions(target_type, target_id):
        """API endpoint to get emoji reactions for a target"""
        try:
            reactions = EmojiReaction.query.filter_by(target_type=target_type, target_id=target_id).all()
            
            # Group reactions by emoji code for counting
            reaction_counts = {}
            for reaction in reactions:
                emoji_code = reaction.emoji_code
                if emoji_code not in reaction_counts:
                    reaction_counts[emoji_code] = {
                        'count': 0,
                        'users': []
                    }
                reaction_counts[emoji_code]['count'] += 1
                reaction_counts[emoji_code]['users'].append(reaction.user_id)
                
            # Format the response
            formatted_reactions = [
                {
                    'emoji_code': emoji_code,
                    'count': data['count'],
                    'users': data['users'],
                    'reacted_by_current_user': current_user.is_authenticated and current_user.id in data['users']
                }
                for emoji_code, data in reaction_counts.items()
            ]
            
            return jsonify({
                'success': True,
                'reactions': formatted_reactions
            })
        except Exception as e:
            logger.error(f"Error getting emoji reactions: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to get emoji reactions'
            }), 500
            
    # Knowledge Base API
    @app.route('/api/knowledge-base', methods=['GET'])
    def get_knowledge_base_entries():
        """API endpoint to get knowledge base entries"""
        try:
            category = request.args.get('category', None)
            search_query = request.args.get('query', None)
            
            query = KnowledgeBaseEntry.query
            
            if category:
                query = query.filter_by(category=category)
                
            if search_query:
                search_pattern = f"%{search_query}%"
                query = query.filter(
                    db.or_(
                        KnowledgeBaseEntry.title.ilike(search_pattern),
                        KnowledgeBaseEntry.content.ilike(search_pattern),
                        KnowledgeBaseEntry.tags.ilike(search_pattern)
                    )
                )
                
            entries = query.order_by(KnowledgeBaseEntry.created_at.desc()).all()
            
            return jsonify({
                'success': True,
                'entries': [entry.to_dict() for entry in entries]
            })
        except Exception as e:
            logger.error(f"Error getting knowledge base entries: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve knowledge base entries'
            }), 500
            
    @app.route('/api/knowledge-base/<int:entry_id>', methods=['GET'])
    def get_knowledge_base_entry(entry_id):
        """API endpoint to get a specific knowledge base entry"""
        try:
            entry = KnowledgeBaseEntry.query.get(entry_id)
            
            if not entry:
                return jsonify({
                    'success': False,
                    'message': 'Knowledge base entry not found'
                }), 404
                
            # Increment the views count
            entry.views_count += 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'entry': entry.to_dict()
            })
        except Exception as e:
            logger.error(f"Error getting knowledge base entry {entry_id}: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve knowledge base entry'
            }), 500
            
    @app.route('/api/knowledge-base', methods=['POST'])
    @login_required
    def create_knowledge_base_entry():
        """API endpoint to create a knowledge base entry"""
        try:
            # Only admins can create knowledge base entries
            if not current_user.is_admin():
                return jsonify({
                    'success': False,
                    'message': 'You do not have permission to create knowledge base entries'
                }), 403
                
            data = request.get_json()
            
            if not data or 'title' not in data or 'content' not in data or 'category' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Title, content, and category are required'
                }), 400
                
            # Create new entry
            new_entry = KnowledgeBaseEntry(
                title=data['title'],
                content=data['content'],
                category=data['category'],
                tags=data.get('tags', '[]'),
                source_ticket_id=data.get('source_ticket_id'),
                created_by=current_user.id
            )
            
            db.session.add(new_entry)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'entry': new_entry.to_dict()
            })
        except Exception as e:
            logger.error(f"Error creating knowledge base entry: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to create knowledge base entry'
            }), 500
            
    @app.route('/api/knowledge-base/<int:entry_id>/helpful', methods=['POST'])
    @login_required
    def mark_knowledge_base_entry_helpful(entry_id):
        """API endpoint to mark a knowledge base entry as helpful"""
        try:
            entry = KnowledgeBaseEntry.query.get(entry_id)
            
            if not entry:
                return jsonify({
                    'success': False,
                    'message': 'Knowledge base entry not found'
                }), 404
                
            # Increment the helpful count
            entry.helpful_count += 1
            db.session.commit()
            
            return jsonify({
                'success': True,
                'entry': entry.to_dict()
            })
        except Exception as e:
            logger.error(f"Error marking knowledge base entry {entry_id} as helpful: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to mark entry as helpful'
            }), 500
            
    # Badges API
    @app.route('/api/badges', methods=['GET'])
    @login_required
    def get_badges():
        """API endpoint to get badges"""
        try:
            badges = Badge.query.all()
            return jsonify({
                'success': True,
                'badges': [badge.to_dict() for badge in badges]
            })
        except Exception as e:
            logger.error(f"Error getting badges: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve badges'
            }), 500
    
    @app.route('/api/user/badges', methods=['GET'])
    @login_required
    def get_user_badges():
        """API endpoint to get the current user's badges"""
        try:
            import json
            user_badges = json.loads(current_user.badges_earned or '[]')
            badges = Badge.query.filter(Badge.id.in_(user_badges)).all() if user_badges else []
            
            return jsonify({
                'success': True,
                'badges': [badge.to_dict() for badge in badges]
            })
        except Exception as e:
            logger.error(f"Error getting user badges: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve user badges'
            }), 500

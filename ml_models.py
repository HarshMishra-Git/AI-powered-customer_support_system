import logging
import re
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

class TicketClassifier:
    """ML model for classifying support tickets into categories"""
    
    def __init__(self):
        self.model = Pipeline([
            ('vectorizer', TfidfVectorizer(max_features=1000)),
            ('classifier', MultinomialNB())
        ])
        self.is_trained = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model with historical ticket data"""
        try:
            # Import here to avoid circular imports
            from models import Ticket
            from app import db
            
            # Check if we have enough tickets in the database
            ticket_count = db.session.query(Ticket).count()
            
            if ticket_count >= 10:  # Arbitrary threshold for minimum training data
                # Get tickets from database
                tickets = db.session.query(Ticket).all()
                descriptions = [ticket.description for ticket in tickets]
                categories = [ticket.issue_category for ticket in tickets]
                
                # Train the model
                self.train(descriptions, categories)
                logger.info("TicketClassifier trained with database data")
            else:
                # Use preset categories for initial classification
                self._initialize_with_preset_data()
                logger.info("TicketClassifier initialized with preset data")
        except Exception as e:
            logger.error(f"Error initializing TicketClassifier: {str(e)}")
            self._initialize_with_preset_data()
    
    def _initialize_with_preset_data(self):
        """Initialize with preset data from the text files"""
        # Predefined categories based on the uploaded files
        categories = [
            "Software Installation Failure",
            "Network Connectivity Issue",
            "Device Compatibility Error",
            "Account Synchronization Bug",
            "Payment Gateway Integration Failure"
        ]
        
        # Sample descriptions from the uploaded files
        descriptions = [
            "I've been trying to install the latest update for your design software for hours. It keeps failing at 75% with an 'unknown error.'",
            "I'm having an issue where my app keeps saying 'no internet connection,' but my Wi-Fi is working fine. Other apps load normally.",
            "Your smart home app crashes every time I try to connect my older thermostat model. It worked fine on my old phone!",
            "My project data isn't syncing between my laptop and tablet. Changes on one device don't show up on the other.",
            "Your API is rejecting our payment gateway integration. Error: 'Invalid SSL certificate.' Our cert is valid and up-to-date!"
        ]
        
        # Create synthetic training data by generating variations
        train_descriptions = []
        train_categories = []
        
        for i, desc in enumerate(descriptions):
            # Add the original
            train_descriptions.append(desc)
            train_categories.append(categories[i])
            
            # Add variations
            words = desc.split()
            if len(words) > 8:
                # Create variations by removing some words
                for _ in range(3):
                    remove_indices = np.random.choice(len(words), size=2, replace=False)
                    variation = ' '.join([w for i, w in enumerate(words) if i not in remove_indices])
                    train_descriptions.append(variation)
                    train_categories.append(categories[i])
        
        # Train with this initial data
        self.train(train_descriptions, train_categories)
    
    def train(self, descriptions, categories):
        """Train the classifier model"""
        try:
            self.model.fit(descriptions, categories)
            self.is_trained = True
            logger.info("TicketClassifier training successful")
        except Exception as e:
            logger.error(f"Error training TicketClassifier: {str(e)}")
    
    def predict_category(self, description):
        """Predict the category of a ticket based on its description"""
        if not self.is_trained:
            # Return a default category if not trained
            return "General Technical Issue"
        
        try:
            # Predict category
            category = self.model.predict([description])[0]
            logger.debug(f"Predicted category: {category}")
            return category
        except Exception as e:
            logger.error(f"Error predicting category: {str(e)}")
            return "General Technical Issue"


class ResolutionPredictor:
    """ML model for predicting resolutions for tickets"""
    
    def __init__(self):
        self.model = Pipeline([
            ('vectorizer', TfidfVectorizer(max_features=1000)),
            ('classifier', RandomForestClassifier(n_estimators=100))
        ])
        self.is_trained = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model with historical resolution data"""
        try:
            # Import here to avoid circular imports
            from models import Ticket
            from app import db
            
            # Check if we have enough tickets with resolutions
            ticket_count = db.session.query(Ticket).filter(Ticket.resolution.isnot(None)).count()
            
            if ticket_count >= 10:  # Arbitrary threshold for minimum training data
                # Get tickets from database
                tickets = db.session.query(Ticket).filter(Ticket.resolution.isnot(None)).all()
                descriptions = [ticket.description for ticket in tickets]
                categories = [ticket.issue_category for ticket in tickets]
                resolutions = [ticket.resolution for ticket in tickets]
                
                # Train the model
                self.train(descriptions, categories, resolutions)
                logger.info("ResolutionPredictor trained with database data")
            else:
                # Use preset data for initial predictions
                self._initialize_with_preset_data()
                logger.info("ResolutionPredictor initialized with preset data")
        except Exception as e:
            logger.error(f"Error initializing ResolutionPredictor: {str(e)}")
            self._initialize_with_preset_data()
    
    def _initialize_with_preset_data(self):
        """Initialize with preset data from the CSV file"""
        try:
            # Define categories and corresponding solutions from the historical data
            categories_and_solutions = {
                "Software Installation Failure": [
                    "Disable antivirus and retry installation",
                    "Download from direct link",
                    "Update to latest version of antivirus"
                ],
                "Network Connectivity Issue": [
                    "Check app permissions for Local Network",
                    "Clear app cache and relog",
                    "Reinstall the app"
                ],
                "Device Compatibility Error": [
                    "Rollback app to version 4.9",
                    "Offer a discount on a compatible thermostat",
                    "Contact thermostat support for an update"
                ],
                "Account Synchronization Bug": [
                    "Reset sync token manually",
                    "Force Full Sync on both devices",
                    "Clear app cache and relog"
                ],
                "Payment Gateway Integration Failure": [
                    "Upgrade server to TLS 1.3",
                    "Verify SSL certificate settings",
                    "Use a different gateway API",
                    "Check server firewall settings"
                ]
            }
            
            # Sample descriptions
            sample_descriptions = {
                "Software Installation Failure": "I'm trying to install your software but it keeps failing during installation.",
                "Network Connectivity Issue": "The app says no internet connection even though my internet is working fine.",
                "Device Compatibility Error": "Your app crashes when I try to connect my device to it.",
                "Account Synchronization Bug": "My data isn't syncing between my devices. Changes don't appear on other devices.",
                "Payment Gateway Integration Failure": "We can't integrate with your payment gateway, it's rejecting our connections."
            }
            
            # Create training data
            train_descriptions = []
            train_categories = []
            train_resolutions = []
            
            for category, solutions in categories_and_solutions.items():
                base_description = sample_descriptions[category]
                
                # Add variations of descriptions for each solution
                for solution in solutions:
                    train_descriptions.append(base_description)
                    train_categories.append(category)
                    train_resolutions.append(solution)
                    
                    # Create some variations
                    words = base_description.split()
                    if len(words) > 5:
                        # Create variations by changing some words
                        variation = base_description.replace("I'm", "I am")
                        train_descriptions.append(variation)
                        train_categories.append(category)
                        train_resolutions.append(solution)
            
            # Train with this initial data
            self.train(train_descriptions, train_categories, train_resolutions)
        except Exception as e:
            logger.error(f"Error initializing ResolutionPredictor with preset data: {str(e)}")
    
    def train(self, descriptions, categories, resolutions):
        """Train the resolution prediction model"""
        try:
            # Create features by combining description and category
            features = [f"{d} [Category: {c}]" for d, c in zip(descriptions, categories)]
            
            self.model.fit(features, resolutions)
            self.is_trained = True
            logger.info("ResolutionPredictor training successful")
        except Exception as e:
            logger.error(f"Error training ResolutionPredictor: {str(e)}")
    
    def predict_resolution(self, description, category):
        """Predict the resolution for a ticket"""
        if not self.is_trained:
            return "Please contact our support team for assistance with this issue."
        
        try:
            # Create feature by combining description and category
            feature = f"{description} [Category: {category}]"
            
            # Predict resolution
            resolution = self.model.predict([feature])[0]
            logger.debug(f"Predicted resolution: {resolution}")
            return resolution
        except Exception as e:
            logger.error(f"Error predicting resolution: {str(e)}")
            return "Please contact our support team for assistance with this issue."

class SentimentAnalyzer:
    """Model for analyzing sentiment in customer messages"""
    
    def __init__(self):
        self.sentiment_categories = [
            "Neutral", "Frustrated", "Confused", "Anxious", 
            "Annoyed", "Urgent", "Satisfied"
        ]
        
        self.sentiment_keywords = {
            "Frustrated": ["frustrated", "annoying", "disappointing", "terrible", "awful", "useless"],
            "Confused": ["confused", "confusing", "unsure", "don't understand", "unclear", "lost"],
            "Anxious": ["anxious", "worried", "concerned", "nervous", "urgent", "critical"],
            "Annoyed": ["annoyed", "irritated", "bothered", "fed up", "tired of", "annoying"],
            "Urgent": ["urgent", "emergency", "immediately", "asap", "critical", "serious"],
            "Satisfied": ["satisfied", "happy", "pleased", "good", "great", "excellent"]
        }
        
        # Emoji suggestions based on sentiment
        self.emoji_suggestions = {
            "Neutral": ["😊", "👋", "👍"],
            "Frustrated": ["😓", "🙁", "🤔"],
            "Confused": ["🤔", "❓", "🧐"],
            "Anxious": ["😟", "⏱️", "🙏"],
            "Annoyed": ["😕", "🙁", "🤨"],
            "Urgent": ["⚠️", "🚨", "⏰"],
            "Satisfied": ["😀", "🎉", "👍"]
        }
        
        # Animation reactions based on sentiment
        self.reaction_animations = {
            "Neutral": "neutral-pulse",
            "Frustrated": "gentle-calm",
            "Confused": "thinking-bubble",
            "Anxious": "reassuring-nod",
            "Annoyed": "apologetic-bow",
            "Urgent": "quick-response",
            "Satisfied": "celebration-confetti"
        }
    
    def analyze_sentiment(self, text):
        """Analyze the sentiment of a text with enhanced features"""
        text = text.lower()
        
        # Count occurrences of sentiment keywords
        sentiment_scores = {category: 0 for category in self.sentiment_categories}
        sentiment_scores["Neutral"] = 1  # Default score
        
        for category, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    sentiment_scores[category] += 1
        
        # Find the sentiment with the highest score
        max_score = 0
        max_sentiment = "Neutral"
        
        for sentiment, score in sentiment_scores.items():
            if score > max_score:
                max_score = score
                max_sentiment = sentiment
        
        # Calculate sentiment intensity (0-100)
        total_score = sum(sentiment_scores.values())
        intensity = min(100, int((max_score / (total_score if total_score > 0 else 1)) * 100))
        
        return {
            "sentiment": max_sentiment,
            "intensity": intensity,
            "emoji_suggestions": self.emoji_suggestions.get(max_sentiment, ["😊"]),
            "reaction_animation": self.reaction_animations.get(max_sentiment, "neutral-pulse"),
            "confidence": max_score / (total_score if total_score > 0 else 1)
        }
        
    def get_emoji_suggestions(self, sentiment):
        """Get emoji suggestions based on sentiment"""
        return self.emoji_suggestions.get(sentiment, ["😊", "👋", "👍"])
        
    def get_reaction_animation(self, sentiment):
        """Get reaction animation based on sentiment"""
        return self.reaction_animations.get(sentiment, "neutral-pulse")


class ConversationHealthAnalyzer:
    """Analyze conversation health and user satisfaction"""
    
    def __init__(self):
        self.health_metrics = {
            "response_time": [],        # Response times in seconds
            "resolution_rate": 0,       # Percentage of conversations resolved
            "user_satisfaction": [],    # User satisfaction ratings (1-5)
            "escalation_rate": 0,       # Percentage of conversations escalated
            "message_count": 0,         # Total number of messages
            "avg_message_length": 0,    # Average message length
            "sentiment_distribution": {} # Distribution of sentiments
        }
        self.sentiment_analyzer = SentimentAnalyzer()
        
    def analyze_conversation(self, conversation_history):
        """Analyze a conversation and return health metrics"""
        if not conversation_history:
            return {"health_score": 0, "metrics": {}}
            
        # Reset metrics for this analysis
        metrics = {
            "response_time": 0,        
            "user_messages": 0,
            "agent_messages": 0,
            "total_messages": len(conversation_history),
            "user_sentiment": "Neutral",
            "agent_sentiment": "Neutral",
            "question_answer_pairs": 0
        }
        
        user_messages = [msg for msg in conversation_history if msg["sender"] == "user"]
        agent_messages = [msg for msg in conversation_history if msg["sender"] == "agent"]
        
        metrics["user_messages"] = len(user_messages)
        metrics["agent_messages"] = len(agent_messages)
        
        # Calculate response times
        response_times = []
        for i in range(1, len(conversation_history)):
            if conversation_history[i]["sender"] == "agent" and conversation_history[i-1]["sender"] == "user":
                time_diff = (conversation_history[i]["timestamp"] - conversation_history[i-1]["timestamp"]).total_seconds()
                response_times.append(time_diff)
        
        if response_times:
            metrics["response_time"] = sum(response_times) / len(response_times)
        
        # Analyze sentiment of last 3 user messages
        if user_messages:
            recent_messages = user_messages[-3:] if len(user_messages) >= 3 else user_messages
            sentiments = [self.sentiment_analyzer.analyze_sentiment(msg["message"]) for msg in recent_messages]
            metrics["user_sentiment"] = sentiments[-1]["sentiment"] if sentiments else "Neutral"
            metrics["sentiment_timeline"] = [s["sentiment"] for s in sentiments]
        
        # Calculate health score (0-100)
        health_score = self._calculate_health_score(metrics)
        
        return {
            "health_score": health_score,
            "metrics": metrics,
            "improvement_suggestions": self._generate_improvement_suggestions(metrics, health_score)
        }
    
    def _calculate_health_score(self, metrics):
        """Calculate a conversation health score from 0-100"""
        score = 70  # Default baseline score
        
        # Adjust based on response time
        if metrics["response_time"] > 0:
            if metrics["response_time"] < 30:  # Fast response under 30 seconds
                score += 10
            elif metrics["response_time"] > 120:  # Slow response over 2 minutes
                score -= 10
        
        # Adjust based on sentiment
        if metrics["user_sentiment"] == "Satisfied":
            score += 15
        elif metrics["user_sentiment"] in ["Frustrated", "Annoyed", "Urgent"]:
            score -= 15
        
        # Adjust based on message ratio
        if metrics["user_messages"] > 0 and metrics["agent_messages"] > 0:
            ratio = metrics["agent_messages"] / metrics["user_messages"]
            if 0.8 <= ratio <= 1.2:  # Balanced conversation
                score += 5
            elif ratio < 0.5:  # Agent not responsive enough
                score -= 10
        
        return max(0, min(100, score))
    
    def _generate_improvement_suggestions(self, metrics, health_score):
        """Generate suggestions for improving conversation health"""
        suggestions = []
        
        if health_score < 40:
            suggestions.append("Critical: Consider immediate supervisor review of this conversation")
        
        if metrics["response_time"] > 120:
            suggestions.append("Improve response time - current average is too high")
            
        if metrics["user_sentiment"] in ["Frustrated", "Annoyed", "Urgent"]:
            suggestions.append("Address customer's emotional state - they seem unhappy")
            
        if metrics["user_messages"] > metrics["agent_messages"] * 2:
            suggestions.append("Increase engagement - customer is sending more messages than agent")
            
        if not suggestions:
            if health_score > 80:
                suggestions.append("Excellent conversation! Consider using as a training example")
            else:
                suggestions.append("Conversation is adequate, but could be improved with more personalization")
                
        return suggestions


class AdvancedResolutionPredictor:
    """Advanced ML model for predicting resolutions with higher accuracy"""
    
    def __init__(self):
        from datetime import datetime
        self.resolution_predictor = ResolutionPredictor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.knowledge_base = {}  # Will store resolved tickets by category for learning
        self.followup_templates = {
            "Network Connectivity Issue": [
                "Have you tried connecting to a different network?",
                "When did you first notice the connectivity problem?",
                "Is this issue happening on all devices or just one?"
            ],
            "Software Installation Failure": [
                "What error messages are you seeing during installation?",
                "Have you tried running the installer as administrator?",
                "Is there enough disk space for the installation?"
            ],
            "Account Synchronization Bug": [
                "When was the last time your account synced successfully?",
                "Are you using the same credentials across all devices?",
                "Have you recently changed your password or security settings?"
            ],
            "Payment Gateway Integration Failure": [
                "What payment provider are you trying to integrate?",
                "Have you verified your API keys are correct?",
                "Are you testing in sandbox mode or production?"
            ],
            "Device Compatibility Error": [
                "What device model are you using?",
                "What operating system version is installed?",
                "Have you installed all available updates for your device?"
            ]
        }
        
    def predict_resolution(self, ticket_data):
        """Predict resolution with advanced features"""
        # Get basic resolution prediction
        basic_prediction = self.resolution_predictor.predict_resolution(
            ticket_data.get("description", ""),
            ticket_data.get("issue_category", "General Support")
        )
        
        # Enhance with knowledge base if available
        category = ticket_data.get("issue_category", "General Support")
        if category in self.knowledge_base and len(self.knowledge_base[category]) > 0:
            # Find similar resolved tickets in knowledge base
            similar_tickets = self._find_similar_tickets(ticket_data, category)
            if similar_tickets:
                # Combine basic prediction with knowledge base solutions
                enhanced_resolution = self._combine_resolutions(basic_prediction, similar_tickets)
                confidence = 0.8  # Higher confidence with knowledge base
            else:
                enhanced_resolution = basic_prediction
                confidence = 0.6
        else:
            enhanced_resolution = basic_prediction
            confidence = 0.5
            
        # Generate smart follow-up questions
        followup_questions = self._generate_followup_questions(ticket_data)
            
        return {
            "resolution": enhanced_resolution,
            "confidence": confidence,
            "followup_questions": followup_questions,
            "quick_actions": self._generate_quick_actions(ticket_data)
        }
        
    def learn_from_resolution(self, ticket_data, successful_resolution):
        """Learn from a successful resolution to improve future predictions"""
        from datetime import datetime
        category = ticket_data.get("issue_category", "General Support")
        
        if category not in self.knowledge_base:
            self.knowledge_base[category] = []
            
        # Add to knowledge base with timestamp
        self.knowledge_base[category].append({
            "description": ticket_data.get("description", ""),
            "resolution": successful_resolution,
            "timestamp": datetime.utcnow()
        })
        
        # Trim knowledge base if it gets too large (keep the 50 most recent entries)
        if len(self.knowledge_base[category]) > 50:
            self.knowledge_base[category] = sorted(
                self.knowledge_base[category], 
                key=lambda x: x["timestamp"], 
                reverse=True
            )[:50]
            
    def _find_similar_tickets(self, ticket_data, category):
        """Find similar tickets in the knowledge base"""
        if category not in self.knowledge_base:
            return []
            
        current_description = ticket_data.get("description", "").lower()
        similar_tickets = []
        
        for entry in self.knowledge_base[category]:
            # Simple keyword matching for now
            # In a real implementation, this would use text embeddings or semantic similarity
            entry_description = entry["description"].lower()
            keywords = set(current_description.split()) & set(entry_description.split())
            similarity = len(keywords) / (len(current_description.split()) + 0.1)
            
            if similarity > 0.2:  # Arbitrary threshold
                similar_tickets.append({
                    "resolution": entry["resolution"],
                    "similarity": similarity
                })
                
        # Sort by similarity
        return sorted(similar_tickets, key=lambda x: x["similarity"], reverse=True)[:3]
        
    def _combine_resolutions(self, basic_resolution, similar_tickets):
        """Combine basic resolution with knowledge base solutions"""
        if not similar_tickets:
            return basic_resolution
            
        # Start with the basic resolution
        combined = basic_resolution
        
        # Add insights from similar tickets
        combined += "\n\nBased on similar issues that were resolved successfully:\n"
        for idx, ticket in enumerate(similar_tickets, 1):
            # Extract the first sentence or up to 100 chars from the similar resolution
            similar_res = ticket["resolution"]
            if len(similar_res) > 100:
                similar_res = similar_res[:100] + "..."
            combined += f"{idx}. {similar_res}\n"
            
        return combined
        
    def _generate_followup_questions(self, ticket_data):
        """Generate smart follow-up questions based on ticket category"""
        category = ticket_data.get("issue_category", "General Support")
        description = ticket_data.get("description", "").lower()
        
        # Get template questions for this category
        template_questions = self.followup_templates.get(category, [
            "Can you provide more details about your issue?",
            "When did you first encounter this problem?",
            "What have you already tried to resolve this?"
        ])
        
        # Filter questions that might already be answered in the description
        followup_questions = []
        for question in template_questions:
            key_terms = set(question.lower().split()) - {"you", "your", "the", "a", "an", "is", "are", "have", "has", "been", "did", "do"}
            already_answered = any(term in description for term in key_terms if len(term) > 3)
            if not already_answered:
                followup_questions.append(question)
                
        # Return up to 3 questions
        return followup_questions[:3]
        
    def _generate_quick_actions(self, ticket_data):
        """Generate quick action buttons based on ticket category"""
        category = ticket_data.get("issue_category", "General Support")
        
        # Default quick actions
        quick_actions = [{
            "label": "Escalate to Supervisor",
            "action": "escalate",
            "style": "warning"
        }]
        
        # Category-specific actions
        if "Network" in category:
            quick_actions.extend([
                {"label": "Run Network Diagnostics", "action": "run_diagnostics", "style": "primary"},
                {"label": "Send Network Reset Guide", "action": "send_guide", "style": "info"}
            ])
        elif "Software" in category:
            quick_actions.extend([
                {"label": "Verify System Requirements", "action": "verify_requirements", "style": "primary"},
                {"label": "Send Clean Installation Steps", "action": "send_steps", "style": "info"}
            ])
        elif "Account" in category:
            quick_actions.extend([
                {"label": "Verify Account Status", "action": "verify_account", "style": "primary"},
                {"label": "Reset User Permissions", "action": "reset_permissions", "style": "info"}
            ])
        elif "Payment" in category:
            quick_actions.extend([
                {"label": "Verify Payment Details", "action": "verify_payment", "style": "primary"},
                {"label": "Process Manual Refund", "action": "process_refund", "style": "danger"}
            ])
        elif "Device" in category:
            quick_actions.extend([
                {"label": "Check Compatibility", "action": "check_compatibility", "style": "primary"},
                {"label": "Send Update Instructions", "action": "send_instructions", "style": "info"}
            ])
        
        return quick_actions


class CollaborativeAgentSystem:
    """System for real-time collaboration between support agents"""
    
    def __init__(self):
        self.active_sessions = {}  # Map of ticket_id to list of agent_ids
        self.agent_status = {}     # Map of agent_id to status
        self.session_notes = {}    # Collaborative notes for each session
        
    def join_session(self, ticket_id, agent_id, agent_name, agent_role):
        """Add an agent to a collaborative session"""
        if ticket_id not in self.active_sessions:
            self.active_sessions[ticket_id] = []
            self.session_notes[ticket_id] = []
            
        # Add agent if not already in session
        if agent_id not in self.active_sessions[ticket_id]:
            self.active_sessions[ticket_id].append(agent_id)
            
        # Update agent status
        self.agent_status[agent_id] = {
            "name": agent_name,
            "role": agent_role,
            "status": "active",
            "joined_at": datetime.utcnow(),
            "current_ticket": ticket_id
        }
        
        # Add session note
        self.add_session_note(
            ticket_id, 
            f"Agent {agent_name} ({agent_role}) joined the session", 
            "system"
        )
        
        return {
            "success": True,
            "active_agents": len(self.active_sessions[ticket_id]),
            "message": f"Successfully joined session for ticket {ticket_id}"
        }
        
    def leave_session(self, ticket_id, agent_id):
        """Remove an agent from a collaborative session"""
        if ticket_id in self.active_sessions and agent_id in self.active_sessions[ticket_id]:
            self.active_sessions[ticket_id].remove(agent_id)
            
            if agent_id in self.agent_status:
                agent_name = self.agent_status[agent_id]["name"]
                agent_role = self.agent_status[agent_id]["role"]
                self.agent_status[agent_id]["status"] = "available"
                self.agent_status[agent_id]["current_ticket"] = None
                
                # Add session note
                self.add_session_note(
                    ticket_id, 
                    f"Agent {agent_name} ({agent_role}) left the session", 
                    "system"
                )
                
        return {
            "success": True,
            "active_agents": len(self.active_sessions.get(ticket_id, [])),
            "message": f"Successfully left session for ticket {ticket_id}"
        }
        
    def get_active_agents(self, ticket_id):
        """Get list of agents currently working on a ticket"""
        if ticket_id not in self.active_sessions:
            return []
            
        agents = []
        for agent_id in self.active_sessions[ticket_id]:
            if agent_id in self.agent_status:
                agents.append(self.agent_status[agent_id])
                
        return agents
        
    def add_session_note(self, ticket_id, note_text, author_id):
        """Add a collaborative note to a session"""
        if ticket_id not in self.session_notes:
            self.session_notes[ticket_id] = []
            
        self.session_notes[ticket_id].append({
            "note": note_text,
            "author": author_id,
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "note_count": len(self.session_notes[ticket_id]),
            "message": "Note added successfully"
        }
        
    def get_session_notes(self, ticket_id):
        """Get all notes for a collaborative session"""
        return self.session_notes.get(ticket_id, [])

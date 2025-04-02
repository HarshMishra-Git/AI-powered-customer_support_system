import logging
import json
import random
import requests
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models import Ticket, Solution, Conversation
from app import db
from ml_models import TicketClassifier, ResolutionPredictor, SentimentAnalyzer

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API for LLM capabilities"""
    def __init__(self, base_url=None):
        # If no base URL is provided, try different endpoints
        self.base_url = base_url or self._get_available_endpoint()
        self.model = "llama3.2"  # Default model, can be changed
        self.is_available = self._check_availability()
        if not self.is_available:
            logger.warning("Ollama server not available - using fallback mode")
    
    def _get_available_endpoint(self):
        """Try different endpoints to find an available Ollama server"""
        endpoints = [
            "http://localhost:11434",
            "http://host.docker.internal:11434",
            "http://ollama:11434"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{endpoint}/api/version", timeout=1)
                if response.status_code == 200:
                    logger.info(f"Found Ollama server at {endpoint}")
                    return endpoint
            except:
                continue
        
        logger.warning("No Ollama server found, using default endpoint")
        return "http://localhost:11434"  # Default fallback
    
    def _check_availability(self):
        """Check if Ollama API is available"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt, system_prompt=None):
        """Generate a response using the Ollama API or fallback to rule-based responses"""
        # If Ollama is not available, use rule-based fallback responses
        if not self.is_available:
            return self._generate_fallback_response(prompt, system_prompt)
            
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return self._generate_fallback_response(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return self._generate_fallback_response(prompt, system_prompt)
    
    def _generate_fallback_response(self, prompt, system_prompt=None):
        """Generate a rule-based fallback response when Ollama is not available"""
        # Simple keyword matching for common queries
        prompt_lower = prompt.lower()
        
        # Check if this is a greeting
        if any(greeting in prompt_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm your support assistant. How can I help you today?"
            
        # Check if asking about capabilities
        if "what can you" in prompt_lower or "help me with" in prompt_lower:
            return "I can help with technical support issues, create tickets for you, and provide solutions for common problems."
            
        # Check for common issue types
        if "network" in prompt_lower or "connection" in prompt_lower or "wifi" in prompt_lower:
            return "It sounds like you're having network connectivity issues. I'd recommend checking your network settings, restarting your router, and ensuring your device is within range of your WiFi signal."
            
        if "install" in prompt_lower or "download" in prompt_lower:
            return "For installation issues, please try the following steps: 1) Make sure your system meets the minimum requirements, 2) Close any conflicting applications, 3) Try running the installer as administrator."
            
        if "account" in prompt_lower or "login" in prompt_lower or "password" in prompt_lower:
            return "For account issues, you can try to: 1) Reset your password, 2) Clear your browser cookies, 3) Ensure you're using the correct username or email address."
            
        # Default fallback response for other queries
        return "I understand you need assistance. To help you better, could you provide more details about your issue? In the meantime, I've created a support ticket for you, and one of our agents will follow up soon."

    def get_embeddings(self, text):
        """Get embeddings for a given text"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            
            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                logger.error(f"Ollama embedding API error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            return []

class ClassifierAgent:
    """Agent responsible for classifying tickets into categories"""
    def __init__(self):
        self.classifier = TicketClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ollama_client = OllamaClient()
    
    def classify_ticket(self, description):
        """Classify a ticket based on its description"""
        category = self.classifier.predict_category(description)
        sentiment_analysis = self.sentiment_analyzer.analyze_sentiment(description)
        
        # Extract the sentiment value from the sentiment analysis result
        sentiment_value = None
        if isinstance(sentiment_analysis, dict) and "sentiment" in sentiment_analysis:
            sentiment_value = sentiment_analysis["sentiment"]
        else:
            sentiment_value = "Neutral"  # Default if we can't determine sentiment
        
        priority = self._determine_priority(sentiment_analysis, description)
        
        # Generate summary and extract actions (new features)
        summary = self._generate_summary(description)
        actions = self._extract_actions(description, category)
        estimated_time = self._estimate_resolution_time(category, description, priority)
        team_assignment = self._assign_team(category, description)
        
        return {
            "issue_category": category,
            "sentiment": sentiment_value,  # Store just the sentiment value string
            "priority": priority,
            "summary": summary,
            "extracted_actions": actions,
            "estimated_resolution_time": estimated_time,
            "team_id": team_assignment
        }
    
    def _determine_priority(self, sentiment, description):
        """Determine ticket priority based on sentiment and description"""
        # Check for urgent keywords
        urgent_keywords = ["urgent", "critical", "emergency", "immediately", "asap", "broken", "error", "not working"]
        
        # Check if any urgent keyword exists in the description
        description_lower = description.lower()
        if any(keyword in description_lower for keyword in urgent_keywords):
            return "Critical"
            
        # Get sentiment value - could be a string or a dictionary from SentimentAnalyzer
        sentiment_value = sentiment
        if isinstance(sentiment, dict) and "sentiment" in sentiment:
            sentiment_value = sentiment["sentiment"]
            
        # Determine based on sentiment value
        if sentiment_value in ["Urgent", "Frustrated", "Annoyed"]:
            return "High"
        elif sentiment_value in ["Anxious", "Confused"]:
            return "Medium"
        else:
            # Apply additional heuristics to avoid everything defaulting to Low
            
            # Network-related words suggest Medium priority
            network_keywords = ["network", "connection", "internet", "wifi", "connect", "slow"]
            if any(keyword in description_lower for keyword in network_keywords):
                return "Medium"
                
            # Account issues are often High priority
            account_keywords = ["account", "password", "login", "locked", "security"]
            if any(keyword in description_lower for keyword in account_keywords):
                return "High"
                
            # Payment issues are Critical or High
            payment_keywords = ["payment", "charge", "refund", "billing", "invoice", "money"]
            if any(keyword in description_lower for keyword in payment_keywords):
                if "not" in description_lower or "failed" in description_lower:
                    return "Critical"
                return "High"
                
            # Application-specific issues
            app_keywords = ["crash", "bug", "glitch", "freeze", "stuck"]
            if any(keyword in description_lower for keyword in app_keywords):
                return "Medium"
                
            # For general questions, feedback, or unclear issues
            return "Low"
    
    def _generate_summary(self, description):
        """Generate a concise summary of the ticket description"""
        if not description:
            return ""
            
        if self.ollama_client.is_available:
            system_prompt = """
            You are an AI assistant that summarizes customer support tickets.
            Create a concise 1-2 sentence summary that captures the main issue.
            Focus on the key problem and what the customer needs.
            """
            
            prompt = f"Summarize this customer support ticket:\n\n{description}"
            summary = self.ollama_client.generate(prompt, system_prompt)
            
            # Ensure the summary is not too long
            if len(summary) > 200:
                summary = summary[:197] + "..."
                
            return summary
        else:
            # Fallback simple summarization - take first 2 sentences or 150 chars
            sentences = description.split('.')
            if len(sentences) > 1:
                return sentences[0].strip() + "." + sentences[1].strip() + "."
            else:
                return description[:150] + "..." if len(description) > 150 else description
    
    def _extract_actions(self, description, category):
        """Extract required actions from ticket description"""
        if self.ollama_client.is_available:
            system_prompt = """
            You are an AI assistant that extracts actionable steps from customer support tickets.
            List 1-3 specific actions that support agents need to take to resolve this issue.
            Format as a numbered list. Be specific and concise.
            """
            
            prompt = f"""
            Category: {category}
            Description: {description}
            
            Extract the necessary actions to resolve this support ticket:
            """
            
            actions = self.ollama_client.generate(prompt, system_prompt)
            return actions
        else:
            # Fallback action extraction based on category
            if "network" in category.lower():
                return "1. Check network connectivity\n2. Verify router settings\n3. Test connection speed"
            elif "software" in category.lower():
                return "1. Verify software version\n2. Check for updates\n3. Verify system requirements"
            elif "account" in category.lower():
                return "1. Verify account credentials\n2. Check account permissions\n3. Reset account if needed"
            else:
                return "1. Gather more information\n2. Identify specific issue\n3. Provide solution steps"
    
    def _estimate_resolution_time(self, category, description, priority):
        """Estimate the resolution time for a ticket in hours"""
        # Base resolution times by category (in hours)
        base_times = {
            "Network Connectivity Issue": 2.0,
            "Software Installation Failure": 1.5,
            "Account Synchronization Bug": 1.0,
            "Payment Gateway Integration Failure": 3.0,
            "Device Compatibility Error": 2.5,
            "General Issue": 1.0
        }
        
        # Priority multipliers
        priority_multipliers = {
            "Critical": 0.5,  # Fastest resolution due to highest priority
            "High": 0.8,
            "Medium": 1.0,
            "Low": 1.5
        }
        
        # Get base time for the category, default to 2 hours if not found
        base_time = base_times.get(category, 2.0)
        
        # Apply priority multiplier
        multiplier = priority_multipliers.get(priority, 1.0)
        
        # Calculate estimated time
        estimated_time = base_time * multiplier
        
        # Check for complexity indicators in the description to adjust time
        complexity_indicators = ["complex", "multiple", "several", "failed repeatedly", "tried everything"]
        if any(indicator in description.lower() for indicator in complexity_indicators):
            estimated_time *= 1.5
            
        return round(estimated_time, 1)  # Round to 1 decimal place
    
    def _assign_team(self, category, description):
        """Assign the ticket to the appropriate team based on category and description"""
        # Default team mapping by category
        category_team_mapping = {
            "Network Connectivity Issue": "NETWORK",
            "Software Installation Failure": "SOFTWARE",
            "Account Synchronization Bug": "ACCOUNT",
            "Payment Gateway Integration Failure": "PAYMENT",
            "Device Compatibility Error": "TECH_SUPPORT"
        }
        
        # Check for specific keywords that might override the default category assignment
        if "payment" in description.lower() or "transaction" in description.lower() or "credit card" in description.lower():
            return "PAYMENT"
            
        if "network" in description.lower() or "internet" in description.lower() or "connection" in description.lower():
            return "NETWORK"
            
        if "account" in description.lower() or "login" in description.lower() or "password" in description.lower():
            return "ACCOUNT"
            
        if "install" in description.lower() or "software" in description.lower() or "app" in description.lower():
            return "SOFTWARE"
        
        # Return the default team for the category, or general support if not found
        return category_team_mapping.get(category, "TECH_SUPPORT")

class ResolutionAgent:
    """Agent responsible for predicting and suggesting solutions"""
    def __init__(self):
        self.predictor = ResolutionPredictor()
        self.ollama_client = OllamaClient()
        self.vectorizer = TfidfVectorizer()
        
        # Don't load solutions in the constructor - will initialize in first use
        self.is_vectorizer_initialized = False
    
    def suggest_solutions(self, ticket):
        """Suggest solutions for a given ticket"""
        # First, check for similar solutions in our database
        similar_solutions = self._find_similar_solutions(ticket)
        
        if similar_solutions:
            # Return the best matches from our database
            return similar_solutions
        else:
            # Generate a new solution using the LLM
            generated_solution = self._generate_solution(ticket)
            return [generated_solution]
    
    def _find_similar_solutions(self, ticket):
        """Find similar solutions from the database"""
        solutions = Solution.query.filter_by(issue_category=ticket.issue_category).all()
        
        if not solutions:
            return []
        
        # Calculate similarity between ticket description and solutions
        solution_texts = [s.solution_text for s in solutions]
        
        try:
            # Initialize vectorizer if not already done
            if not self.is_vectorizer_initialized:
                all_solutions = Solution.query.all()
                if all_solutions:
                    all_texts = [s.solution_text for s in all_solutions]
                    self.vectorizer.fit(all_texts)
                    self.is_vectorizer_initialized = True
                else:
                    # If no solutions in DB, just fit on current solutions
                    self.vectorizer.fit(solution_texts)
                    self.is_vectorizer_initialized = True
            
            # Now do the transformation
            solution_vectors = self.vectorizer.transform(solution_texts)
            ticket_vector = self.vectorizer.transform([ticket.description])
            
            similarities = cosine_similarity(ticket_vector, solution_vectors)[0]
            
            # Get top 3 most similar solutions
            top_indices = similarities.argsort()[-3:][::-1]
            
            result = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Threshold for similarity
                    result.append(solutions[idx].to_dict())
            
            return result
        except Exception as e:
            logger.error(f"Error finding similar solutions: {str(e)}")
            return []
    
    def _generate_solution(self, ticket):
        """Generate a solution using the LLM"""
        system_prompt = """
        You are an expert customer support agent. Your task is to provide a clear, 
        helpful solution to the customer's issue. Be specific and concise.
        """
        
        prompt = f"""
        Issue Category: {ticket.issue_category}
        Customer's Issue: {ticket.description}
        
        Please provide a step-by-step solution to resolve this issue.
        """
        
        solution_text = self.ollama_client.generate(prompt, system_prompt)
        
        # Create a new solution in the database
        new_solution = Solution(
            issue_category=ticket.issue_category,
            solution_text=solution_text,
            success_rate=0.5,  # Initial success rate
            usage_count=1
        )
        
        try:
            db.session.add(new_solution)
            db.session.commit()
            return new_solution.to_dict()
        except Exception as e:
            logger.error(f"Error saving generated solution: {str(e)}")
            db.session.rollback()
            return {
                "id": None,
                "issue_category": ticket.issue_category,
                "solution_text": solution_text,
                "success_rate": 0.5,
                "usage_count": 0
            }

class EscalationAgent:
    """Agent responsible for determining if a ticket needs human intervention"""
    def __init__(self):
        pass
    
    def should_escalate(self, ticket, conversation_history=None):
        """Determine if a ticket should be escalated to a human agent"""
        # Immediate escalation for Critical priority
        if ticket.priority == "Critical":
            return True, "Critical priority issue requires immediate attention"
        
        # Escalate if multiple conversations without resolution
        if conversation_history and len(conversation_history) > 5:
            return True, "Multiple attempts to resolve without success"
        
        # Escalate based on specific keywords in the description
        escalation_keywords = ["manager", "supervisor", "lawsuit", "legal", "compensation", "refund"]
        if any(keyword in ticket.description.lower() for keyword in escalation_keywords):
            return True, f"Customer mentioned {[k for k in escalation_keywords if k in ticket.description.lower()][0]}"
        
        return False, "Automated handling is sufficient"

class FeedbackAgent:
    """Agent responsible for collecting and learning from customer feedback"""
    def __init__(self):
        pass
    
    def process_feedback(self, ticket_id, rating, comment):
        """Process feedback for a ticket"""
        # Update solution success rate if applicable
        ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
        
        if not ticket or not ticket.resolution:
            return False
        
        # Find the solution that matches this resolution
        solution = Solution.query.filter_by(solution_text=ticket.resolution).first()
        
        if solution:
            # Update success rate based on new feedback
            old_success_total = solution.success_rate * solution.usage_count
            
            # Normalize rating to 0-1 scale (rating is 1-5)
            normalized_rating = rating / 5.0
            
            # Update count and recalculate success rate
            solution.usage_count += 1
            solution.success_rate = (old_success_total + normalized_rating) / solution.usage_count
            
            try:
                db.session.commit()
                return True
            except Exception as e:
                logger.error(f"Error updating solution success rate: {str(e)}")
                db.session.rollback()
                return False
        
        return False

class ChatbotAgent:
    """Agent responsible for handling direct user queries with structured conversation flow"""
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.classifier_agent = ClassifierAgent()
        # Define available issue categories
        self.issue_categories = [
            "Network Connectivity Issue",
            "Software Installation Failure",
            "Account Synchronization Bug",
            "Payment Gateway Integration Failure",
            "Device Compatibility Error",
            "General Technical Support"
        ]
        # Track conversation state
        self.conversation_states = {}  # Will store conversation state by session_id
    
    def respond_to_query(self, user_message, conversation_history=None, session_id=None):
        """Generate a response based on conversation state and user query"""
        if not session_id:
            session_id = "default"
            
        # Initialize conversation state if needed
        if session_id not in self.conversation_states:
            self.conversation_states[session_id] = {
                "state": "greeting",
                "selected_category": None,
                "issue_description": None,
                "ticket_id": None,
                "solution_provided": False,
                "feedback_requested": False,
                "conversation_ending": False,
                "last_agent_message": None
            }
            
        state = self.conversation_states[session_id]
        
        # Check for thank you messages that should end the conversation
        thank_you_phrases = ["thank you", "thanks", "thank", "thx", "appreciate it"]
        if any(phrase in user_message.lower() for phrase in thank_you_phrases) and not state["state"] == "greeting":
            # Mark conversation as ending and return closing message
            state["conversation_ending"] = True
            return {
                "response": "You're welcome! I'm glad I could help. Is there anything else you need assistance with today?",
                "create_ticket": False,
                "ticket_id": state.get("ticket_id"),
                "current_state": "closing"
            }
        
        # Handle simple yes/no responses to "anything else" questions
        if state["conversation_ending"]:
            # If user says no (or similar) to "anything else" question
            no_phrases = ["no", "nope", "that's all", "nothing else", "all set", "i'm good", "im good"]
            yes_phrases = ["yes", "yeah", "yep", "sure", "please", "i do", "i have", "another question"]
            
            if any(no_match == user_message.lower() or user_message.lower().startswith(no_match) for no_match in no_phrases):
                # User doesn't need anything else
                return {
                    "response": "Thank you for using our AI support chat! Feel free to return anytime you need assistance. Have a great day!",
                    "create_ticket": False,
                    "ticket_id": state.get("ticket_id"),
                    "current_state": "closed"
                }
            elif any(yes_match in user_message.lower() for yes_match in yes_phrases):
                # User has another question, reset the state but stay in conversation
                state["conversation_ending"] = False
                state["state"] = "greeting"
                state["selected_category"] = None
                state["issue_description"] = None
                # Continue to greeting handling (don't return here)
            else:
                # If response doesn't match yes/no pattern but conversation was ending
                state["conversation_ending"] = False
            
        # Check if this is the first message in the conversation
        if not conversation_history or len(conversation_history) == 0:
            # Reset to greeting state for new conversations
            state["state"] = "greeting"
            
        # Process current message based on conversation state
        if state["state"] == "closing":
            # User is starting a new conversation after the previous one ended
            issue_detected = self._detect_technical_issue(user_message)
            if issue_detected:
                # User is describing a problem directly, classify and move to issue description
                classification = self.classifier_agent.classify_ticket(user_message)
                state["selected_category"] = classification["issue_category"]
                state["issue_description"] = user_message
                state["state"] = "solution_provided"
                state["conversation_ending"] = False
                response = self._handle_issue_description(user_message, session_id)
                create_ticket = False
                return {
                    "response": response,
                    "create_ticket": create_ticket,
                    "ticket_id": state.get("ticket_id"),
                    "current_state": state["state"]
                }
            else:
                # Reset to greeting for a fresh start
                state["state"] = "greeting"
                state["conversation_ending"] = False
            
        if state["state"] == "greeting":
            # If this is a response to initial greeting (not first message), check for tech issue
            if len(user_message) > 3 and conversation_history and len(conversation_history) > 1:
                issue_detected = self._detect_technical_issue(user_message)
                if issue_detected:
                    # User is describing a problem directly, classify and move to issue description
                    classification = self.classifier_agent.classify_ticket(user_message)
                    state["selected_category"] = classification["issue_category"]
                    state["issue_description"] = user_message
                    state["state"] = "solution_provided"
                    response = self._handle_issue_description(user_message, session_id)
                    create_ticket = False
                    return {
                        "response": response,
                        "create_ticket": create_ticket,
                        "ticket_id": state.get("ticket_id"),
                        "current_state": state["state"]
                    }
            
            # Initial greeting, provide category options
            response = self._handle_greeting(session_id)
            create_ticket = False
            
        elif state["state"] == "category_selection":
            # Process category selection
            response = self._handle_category_selection(user_message, session_id)
            create_ticket = False
            
        elif state["state"] == "issue_description":
            # Save issue description and provide solutions
            response = self._handle_issue_description(user_message, session_id)
            create_ticket = False
            
        elif state["state"] == "solution_provided":
            # Ask for feedback on solution
            response = self._handle_solution_feedback(user_message, session_id)
            create_ticket = state.get("create_ticket", False)
            
        elif state["state"] == "feedback_received":
            # Process feedback and create ticket if needed
            response, create_ticket = self._handle_feedback(user_message, session_id)
            
        else:
            # Default fallback for any other state
            issue_detected = self._detect_technical_issue(user_message)
            if issue_detected:
                # Reset to greeting to start fresh, but preserve conversation_ending status
                self.conversation_states[session_id] = {
                    "state": "greeting",
                    "selected_category": None,
                    "issue_description": None,
                    "conversation_ending": False
                }
                response = self._handle_greeting(session_id)
                create_ticket = False
            else:
                # General response
                system_prompt = """
                You are a helpful AI assistant for a technical support team. Be polite, professional and concise.
                If you don't know something, say so clearly. Ask clarifying questions when needed.
                """
                response = self.ollama_client.generate(user_message, system_prompt)
                create_ticket = False
        
        return {
            "response": response,
            "create_ticket": create_ticket,
            "ticket_id": state.get("ticket_id"),
            "current_state": state["state"]  # For debugging
        }
    
    def _handle_greeting(self, session_id):
        """Handle initial greeting"""
        self.conversation_states[session_id]["state"] = "category_selection"
        
        categories_text = "\n".join([f"{i+1}. {category}" for i, category in enumerate(self.issue_categories)])
        
        response = (f"Hello! I'm your AI support assistant. How can I help you today?\n\n"
                   f"Please select the category that best describes your issue:\n\n"
                   f"{categories_text}\n\n"
                   f"Just type the number or name of the category that matches your issue.")
        
        return response
    
    def _handle_category_selection(self, user_message, session_id):
        """Process the user's category selection"""
        category = None
        
        # Check if user entered a number
        try:
            selection_num = int(user_message.strip())
            if 1 <= selection_num <= len(self.issue_categories):
                category = self.issue_categories[selection_num - 1]
        except ValueError:
            # User may have typed the category name
            user_input = user_message.lower().strip()
            for cat in self.issue_categories:
                if cat.lower() in user_input:
                    category = cat
                    break
        
        if category:
            # Valid category selected
            self.conversation_states[session_id]["selected_category"] = category
            self.conversation_states[session_id]["state"] = "issue_description"
            return f"You've selected: {category}. Please describe your issue in detail so I can help you better."
        else:
            # Invalid selection, try again
            categories_text = "\n".join([f"{i+1}. {category}" for i, category in enumerate(self.issue_categories)])
            return (f"I'm sorry, I couldn't understand your selection. Please choose one of the following options:\n\n"
                   f"{categories_text}\n\n"
                   f"Just type the number or name of the category.")
    
    def _handle_issue_description(self, user_message, session_id):
        """Process the user's issue description and provide solutions"""
        state = self.conversation_states[session_id]
        
        # Save the issue description
        state["issue_description"] = user_message
        state["state"] = "solution_provided"
        
        # Determine issue category if not already set
        selected_category = state["selected_category"]
        if not selected_category:
            classification = self.classifier_agent.classify_ticket(user_message)
            selected_category = classification["issue_category"]
            state["selected_category"] = selected_category
        
        # Get troubleshooting steps based on category
        troubleshooting_steps = self._get_troubleshooting_steps(selected_category, user_message)
        
        # Compose response with apology and steps
        response = (f"I'm sorry to hear you're experiencing this issue with {selected_category.lower()}. "
                   f"Let me help you troubleshoot:\n\n{troubleshooting_steps}\n\n"
                   f"Did these steps resolve your issue? (Yes/No)")
        
        return response
    
    def _handle_solution_feedback(self, user_message, session_id):
        """Handle the user's feedback on provided solutions"""
        state = self.conversation_states[session_id]
        
        # Check if issue was resolved
        user_input = user_message.lower().strip()
        issue_resolved = any(word in user_input for word in ["yes", "yeah", "yep", "resolved", "fixed", "solved", "works", "it's resolved", "its resolved"])
        button_resolved = "yes, it's resolved" in user_input or "yes, resolved" in user_input
        
        if issue_resolved or button_resolved:
            # Issue resolved
            state["state"] = "feedback_received"
            state["feedback"] = "resolved"
            return ("Great! I'm glad the issue has been resolved. Is there anything else I can help you with? "
                   "If you have a moment, please rate your experience (1-5 stars).")
        else:
            # Check for explicit button click or text indicating unresolved issue
            not_resolved = any(phrase in user_input for phrase in ["no", "not resolved", "still having issues", "didn't work", "not working"])
            button_not_resolved = "no, still having issues" in user_input
            
            if not_resolved or button_not_resolved:
                # Issue not resolved, create ticket
                state["state"] = "feedback_received"
                state["feedback"] = "unresolved"
                state["create_ticket"] = True
                
                # Ask for any additional details
                return ("I'm sorry those steps didn't resolve your issue. I'll create a support ticket for you so our team can investigate further. "
                       "Is there any additional information you'd like to add to your ticket? "
                       "(If not, just type 'No additional info')")
            else:
                # Unclear response
                state["state"] = "solution_provided"  # Stay in the same state
                return ("I'm not sure if your issue was resolved. Could you please let me know if the troubleshooting steps "
                       "resolved your issue? Please click 'Yes, resolved' if fixed or 'No, still having issues' if you need more help.")
    
    def _handle_feedback(self, user_message, session_id):
        """Process feedback and create ticket if needed"""
        state = self.conversation_states[session_id]
        
        if state["feedback"] == "resolved":
            # Process satisfaction rating
            try:
                rating = int(''.join(filter(str.isdigit, user_message)))
                if 1 <= rating <= 5:
                    response = f"Thank you for your feedback! We've recorded your rating of {rating}/5. Have a great day!"
                else:
                    response = "Thank you for your feedback! Have a great day!"
            except ValueError:
                response = "Thank you for your feedback! Have a great day!"
                
            # Reset conversation state for next issue but preserve conversation_ending flag
            self.conversation_states[session_id] = {
                "state": "closing",  # Use a closing state instead of immediately resetting to greeting
                "selected_category": None,
                "issue_description": None,
                "conversation_ending": True
            }
            return response, False
            
        else:
            # Create support ticket with the collected information
            additional_info = user_message if not user_message.lower().strip() in ["no", "no additional info", "none"] else ""
            
            # Combine original description with additional info
            full_description = state["issue_description"]
            if additional_info:
                full_description += f"\n\nAdditional information: {additional_info}"
            
            # Create the actual ticket
            ticket_data = self.create_ticket_from_chat(full_description, state["selected_category"])
            
            if ticket_data:
                state["ticket_id"] = ticket_data["ticket_id"]
                response = (f"I've created ticket #{ticket_data['ticket_id']} for you. Our support team will review your issue and respond as soon as possible. "
                           f"The estimated resolution time is {ticket_data.get('estimated_resolution_time', 2.0)} hours. "
                           f"You can check the status of your ticket on the Tickets page. Is there anything else I can help you with?")
            else:
                response = "I'm sorry, there was an issue creating your ticket. Please try again or contact our support team directly."
            
            # Reset conversation state for next issue, but preserve state
            self.conversation_states[session_id] = {
                "state": "closing",
                "selected_category": None,
                "issue_description": None,
                "ticket_id": state.get("ticket_id"),
                "conversation_ending": True
            }
            
            return response, True
    
    def _get_troubleshooting_steps(self, category, description):
        """Get troubleshooting steps based on category and description"""
        # Use LLM to generate specific steps if available
        if self.ollama_client.is_available:
            system_prompt = """
            You are an expert technical support agent. Provide 3-5 specific troubleshooting steps for the given
            issue category and description. Format as a numbered list. Keep steps clear and actionable.
            """
            
            prompt = f"""
            Issue Category: {category}
            Issue Description: {description}
            
            Provide troubleshooting steps:
            """
            
            steps = self.ollama_client.generate(prompt, system_prompt)
            return steps
        
        # Fallback troubleshooting steps by category
        if "network" in category.lower():
            return ("1. Restart your router and modem by unplugging them for 30 seconds, then plugging back in\n"
                   "2. Check if other devices can connect to the same network\n"
                   "3. Try connecting to both WiFi and wired connections if possible\n"
                   "4. Reset your network adapter by going to Settings > Network > Reset\n"
                   "5. Contact your internet service provider to check for outages")
                   
        elif "software" in category.lower():
            return ("1. Make sure your system meets the minimum requirements for the software\n"
                   "2. Run the installer as Administrator\n"
                   "3. Temporarily disable any antivirus or firewall that might be blocking installation\n"
                   "4. Clear temporary files and try reinstalling\n"
                   "5. Download a fresh copy of the installer from the official website")
                   
        elif "account" in category.lower():
            return ("1. Log out from all devices and log back in\n"
                   "2. Clear your browser cache and cookies\n"
                   "3. Reset your password using the 'Forgot Password' link\n"
                   "4. Check if your account has been locked for security reasons\n"
                   "5. Verify your email address is correct in your profile settings")
                   
        elif "payment" in category.lower():
            return ("1. Verify your payment information is entered correctly\n"
                   "2. Check if your credit card has sufficient funds and isn't expired\n"
                   "3. Try using a different payment method\n"
                   "4. Check if your bank is blocking the transaction\n"
                   "5. Clear your browser cache and try again in an incognito/private window")
                   
        elif "device" in category.lower():
            return ("1. Check if your device meets the minimum system requirements\n"
                   "2. Update to the latest drivers for your device\n"
                   "3. Update your operating system to the latest version\n"
                   "4. Try using the application in compatibility mode\n"
                   "5. Restart your device and try again")
                   
        else:
            return ("1. Restart your device and try again\n"
                   "2. Clear temporary files and browser cache\n"
                   "3. Check for any error messages and note them down\n"
                   "4. Update any related software to the latest version\n"
                   "5. Check if others are experiencing similar issues")
    
    def _detect_technical_issue(self, message):
        """Detect if a message describes a technical issue"""
        issue_keywords = ["error", "problem", "issue", "not working", "broken", "fails", "bug", "can't", "cannot", "doesn't", "does not"]
        
        if any(keyword in message.lower() for keyword in issue_keywords):
            return True
        
        # For more complex issues, we could use the classifier
        if len(message.split()) > 10:  # Only try to classify longer messages
            classification = self.classifier_agent.classify_ticket(message)
            if classification["issue_category"] != "General Inquiry":
                return True
        
        return False
    
    def create_ticket_from_chat(self, user_message, category=None):
        """Create a ticket from a chat conversation"""
        # Use the classifier agent to categorize the issue
        classification = self.classifier_agent.classify_ticket(user_message)
        
        # Override category if provided
        if category:
            classification["issue_category"] = category
        
        # Generate a unique ticket ID
        next_id = random.randint(100, 999)
        ticket_id = f"TECH_{next_id}"
        
        # Create the ticket with enhanced data
        new_ticket = Ticket(
            ticket_id=ticket_id,
            issue_category=classification["issue_category"],
            sentiment=classification["sentiment"],
            priority=classification["priority"],
            description=user_message,
            status="Open",
            resolution_status="Pending",
            summary=classification.get("summary", ""),
            extracted_actions=classification.get("extracted_actions", ""),
            estimated_resolution_time=classification.get("estimated_resolution_time", 2.0),
            team_id=classification.get("team_id", "TECH_SUPPORT")
        )
        
        try:
            db.session.add(new_ticket)
            db.session.commit()
            
            # Add the initial conversation
            conversation = Conversation(
                ticket_id=ticket_id,
                message=user_message,
                sender="user"
            )
            
            db.session.add(conversation)
            db.session.commit()
            
            return new_ticket.to_dict()
        except Exception as e:
            logger.error(f"Error creating ticket from chat: {str(e)}")
            db.session.rollback()
            return None

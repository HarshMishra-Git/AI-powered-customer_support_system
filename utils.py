import logging
import re
import json
import random
import string
from datetime import datetime

from app import db
from models import KnowledgeBaseEntry, Ticket, Conversation, Feedback

logger = logging.getLogger(__name__)

def generate_ticket_id(prefix="TICKET"):
    """Generate a unique ticket ID with a given prefix"""
    timestamp = datetime.utcnow().strftime("%m%d%H%M")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}_{timestamp}_{random_suffix}"

def extract_error_code(text):
    """Extract error codes from text using regex"""
    # Match common error code formats
    patterns = [
        r'Error: \'([A-Za-z0-9_]+)\'',  # Error: 'CODE'
        r'Error code: ([A-Za-z0-9_]+)',  # Error code: CODE
        r'#([A-Za-z0-9_]+)',  # #CODE
        r'Error ([0-9]+)',  # Error 12345
        r'([A-Z]+-[0-9]+)'  # ABC-12345
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def calculate_priority_score(ticket):
    """Calculate a numerical priority score for a ticket (1-10)"""
    score = 5  # Default medium priority
    
    # Adjust based on explicit priority
    if ticket.priority == "Critical":
        score += 3
    elif ticket.priority == "High":
        score += 2
    elif ticket.priority == "Low":
        score -= 2
    
    # Adjust based on sentiment
    if ticket.sentiment in ["Frustrated", "Annoyed", "Urgent"]:
        score += 1
    
    # Ensure the score is within bounds
    return max(1, min(score, 10))

def format_time_elapsed(seconds):
    """Format elapsed time in seconds to a human-readable string"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours"
    else:
        return f"{int(seconds / 86400)} days"

def summarize_conversation(conversation_history, max_length=200):
    """Create a summarized version of a conversation for logging or display"""
    if not conversation_history:
        return ""
    
    # Take the first message and the last two messages
    messages = []
    if len(conversation_history) > 0:
        messages.append(conversation_history[0])
    
    if len(conversation_history) > 2:
        messages.extend(conversation_history[-2:])
    elif len(conversation_history) > 1:
        messages.append(conversation_history[-1])
    
    # Format each message and join them
    formatted = []
    for msg in messages:
        sender = "Customer" if msg.get('sender') == 'user' else "Agent"
        text = msg.get('message', '')
        if len(text) > 50:
            text = text[:47] + "..."
        formatted.append(f"{sender}: {text}")
    
    summary = " | ".join(formatted)
    
    # Truncate if too long
    if len(summary) > max_length:
        return summary[:max_length-3] + "..."
    
    return summary

def create_knowledge_base_entry_from_ticket(ticket_id, admin_id=1):
    """Create a knowledge base entry from a successfully resolved ticket"""
    try:
        # Get the ticket and its conversations
        ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found")
            return None
            
        # Only create KB entries for resolved tickets
        if ticket.resolution_status != "Resolved" or not ticket.resolution:
            logger.info(f"Ticket {ticket_id} is not resolved or has no resolution")
            return None
            
        # Check feedback - only use tickets with positive feedback
        feedback = Feedback.query.filter_by(ticket_id=ticket_id).order_by(Feedback.timestamp.desc()).first()
        if not feedback or feedback.rating < 4:  # Only use highly rated resolutions (4-5 stars)
            logger.info(f"Ticket {ticket_id} does not have positive feedback")
            return None
            
        # Get conversations
        conversations = Conversation.query.filter_by(ticket_id=ticket_id).order_by(Conversation.timestamp).all()
        if not conversations:
            logger.info(f"Ticket {ticket_id} has no conversations")
            return None
            
        # Extract customer issue from first user message
        user_messages = [c for c in conversations if c.sender == 'user']
        agent_messages = [c for c in conversations if c.sender == 'agent']
        
        if not user_messages or not agent_messages:
            logger.info(f"Ticket {ticket_id} missing user or agent messages")
            return None
            
        # Create title based on ticket category and first message
        issue_summary = user_messages[0].message.split('\n')[0][:50]  # First line of first message
        title = f"{ticket.issue_category.title()}: {issue_summary}"
        
        # Create content with problem and solution
        problem_description = user_messages[0].message
        solution = ticket.resolution
        
        content = f"""# {title}

## Problem Description
{problem_description}

## Solution
{solution}

## Additional Information
- Category: {ticket.issue_category}
- Priority: {ticket.priority}
- Resolution Time: {ticket.estimated_resolution_time} hours
        """
        
        # Extract tags from category and description
        tags = [ticket.issue_category]
        # Add common words as tags
        common_words = set([word.lower() for word in re.findall(r'\b[a-zA-Z]{4,}\b', problem_description)
                           if len(word) > 3 and word.lower() not in ["this", "that", "with", "have", "from"]])
        tags.extend(list(common_words)[:5])  # Limit to 5 additional tags
        
        # Create the knowledge base entry
        entry = KnowledgeBaseEntry(
            title=title,
            content=content,
            category=ticket.issue_category,
            tags=json.dumps(tags),
            source_ticket_id=ticket_id,
            created_by=admin_id,
            views_count=0,
            helpful_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(entry)
        db.session.commit()
        
        logger.info(f"Created knowledge base entry from ticket {ticket_id}: {title}")
        return entry
        
    except Exception as e:
        logger.error(f"Error creating knowledge base entry from ticket {ticket_id}: {str(e)}")
        db.session.rollback()
        return None

def find_knowledge_base_entries_for_issue(description, category=None, limit=3):
    """Find relevant knowledge base entries for a given issue description"""
    try:
        query = KnowledgeBaseEntry.query
        
        # Filter by category if provided
        if category:
            query = query.filter_by(category=category)
            
        # Get all entries
        entries = query.all()
        
        # If no entries found, return empty list
        if not entries:
            return []
            
        # Simple keyword matching for now
        # In a production system, this would use embeddings/cosine similarity
        scored_entries = []
        words = set(re.findall(r'\b[a-zA-Z]{3,}\b', description.lower()))
        
        for entry in entries:
            # Count matching words in title and content
            title_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', entry.title.lower()))
            content_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', entry.content.lower()))
            
            # Try to parse tags
            try:
                tags = set(json.loads(entry.tags))
            except:
                tags = set()
                
            # Calculate score based on matches
            title_matches = len(words.intersection(title_words))
            content_matches = len(words.intersection(content_words))
            tag_matches = sum(1 for tag in tags if tag.lower() in description.lower())
            
            # Weight title matches more heavily
            score = (title_matches * 3) + content_matches + (tag_matches * 2)
            
            # Boost by helpful count
            score += min(5, entry.helpful_count)  # Cap at +5 boost
            
            scored_entries.append((entry, score))
        
        # Sort by score (descending) and return top entries
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, score in scored_entries[:limit]]
        
    except Exception as e:
        logger.error(f"Error finding knowledge base entries: {str(e)}")
        return []

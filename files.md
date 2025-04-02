# Project Files Documentation

This document provides a detailed explanation of each file in the AI-powered customer support system, including their purpose, functionality, and how they interact with other components.

## Core Application Files

### `main.py`
**Purpose**: Main entry point for the Flask application.
**Functionality**:
- Imports the Flask app from app.py
- Runs the application with debugging enabled
- Configures host/port settings for deployment

**Key Code**:
```python
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### `app.py`
**Purpose**: Flask application configuration and database setup.
**Functionality**:
- Creates and configures the Flask application
- Sets up SQLAlchemy with the database
- Configures session security
- Initializes the database connection

**Key Components**:
- `Base` class: SQLAlchemy declarative base for models
- `db` object: SQLAlchemy instance for database operations
- Database URI configuration
- Database initialization and table creation

### `models.py`
**Purpose**: Database models and data structures.
**Functionality**:
- Defines all database tables and relationships
- Implements model methods for authentication and data conversion
- Manages model relationships and constraints

**Key Models**:
1. `User`: User authentication and profile data
   - Includes password hashing and verification
   - Role-based permissions (admin/customer)
   - Theme preferences and profile settings

2. `Ticket`: Support ticket information
   - Core fields like description, status, category
   - AI-generated metadata (sentiment, priority)
   - Relationships to conversations and metrics

3. `Conversation`: Message history for tickets
   - Tracks all messages in ticket threads
   - Maintains sender information and timestamps
   - Provides conversation context for agents

4. `KnowledgeBaseEntry`: Solution repository
   - Structured problem-solution pairs
   - Tags and categorization for retrieval
   - Usage statistics and ratings

5. `Solution`: Model for solution options
   - Tracks solution text and categories
   - Maintains success rates and usage metrics
   - Associates with ticket categories

6. `Feedback`: Customer satisfaction data
   - Captures ratings and comments
   - Links to tickets for context
   - Provides training signals for ML models

7. `Team`: Support team organization
   - Team structure and specializations
   - Workload tracking and assignments
   - Assignment logic for ticket routing

8. Several additional supporting models for metrics, badges, reactions, etc.

### `routes.py`
**Purpose**: API endpoints and view routes.
**Functionality**:
- Defines all web routes and API endpoints
- Initializes AI agents and services
- Implements request handling logic
- Manages authentication and permissions

**Key Route Categories**:
1. **Authentication Routes**:
   - `/login`: User authentication
   - `/register`: New user registration
   - `/logout`: Session termination
   - `/profile`: User profile management

2. **Page Routes**:
   - `/`: Home page
   - `/dashboard`: Admin analytics dashboard
   - `/tickets`: Ticket management interface
   - `/chat`: Chatbot interface
   - `/knowledge-base`: Knowledge repository interface

3. **Ticket API Routes**:
   - `/api/tickets`: Create and list tickets
   - `/api/tickets/<ticket_id>`: Get ticket details
   - `/api/tickets/<ticket_id>/conversation`: Add messages
   - `/api/tickets/<ticket_id>/suggest-solutions`: Get AI solutions
   - `/api/tickets/<ticket_id>/knowledge-base`: Get related knowledge entries
   - `/api/tickets/<ticket_id>/feedback`: Add feedback

4. **Knowledge Base Routes**:
   - `/api/knowledge-base`: Query knowledge entries
   - `/api/knowledge-base/<entry_id>`: Get specific entries
   - `/api/knowledge-base/<entry_id>/helpful`: Mark entries as helpful

5. **Chat and Analytics Routes**:
   - `/api/chat`: Chatbot interaction endpoint
   - `/api/dashboard/stats`: Dashboard analytics
   - `/api/conversation-health`: Conversation quality metrics

### `forms.py`
**Purpose**: Form definitions for web interfaces.
**Functionality**:
- Defines WTForms classes for data validation
- Handles form rendering and processing
- Implements custom validators

**Key Forms**:
1. `LoginForm`: User authentication
2. `RegistrationForm`: New user signup with validation
3. `ProfileUpdateForm`: User profile editing
4. `UserPreferencesForm`: UI customization settings

### `utils.py`
**Purpose**: Utility functions used across the application.
**Functionality**:
- Provides helper functions for common tasks
- Implements shared logic for multiple components
- Handles specialized formatting and processing

**Key Utilities**:
1. `generate_ticket_id()`: Creates unique ticket identifiers
2. `extract_error_code()`: Parses error codes from texts
3. `calculate_priority_score()`: Determines ticket priority levels
4. `format_time_elapsed()`: Formats time differences
5. `summarize_conversation()`: Creates ticket conversation summaries
6. `create_knowledge_base_entry_from_ticket()`: Transforms resolved tickets into KB entries
7. `find_knowledge_base_entries_for_issue()`: Searches KB for relevant solutions

## AI and ML Components

### `agents.py`
**Purpose**: Defines all AI agent classes.
**Functionality**:
- Implements specialized AI agents for different tasks
- Handles natural language processing
- Manages conversation flow and ticket handling

**Key Agents**:
1. `OllamaClient`: Interface for LLM capabilities
   - Connects to Ollama API for language model functionality
   - Handles prompt generation and response processing
   - Provides fallback mechanisms when LLM is unavailable
   - Generates text embeddings for similarity searches

2. `ClassifierAgent`: Categorizes support tickets
   - Analyzes ticket descriptions to determine categories
   - Extracts sentiment for priority determination
   - Generates summaries of ticket content
   - Estimates resolution time and required actions
   - Assigns tickets to appropriate teams

3. `ResolutionAgent`: Suggests solutions for tickets
   - Finds relevant knowledge base entries
   - Retrieves similar previous tickets
   - Generates solution suggestions
   - Ranks solutions by predicted effectiveness
   - Adapts suggestions to specific ticket context

4. `EscalationAgent`: Determines when human intervention is needed
   - Analyzes conversation patterns and complexity
   - Detects customer frustration signals
   - Identifies topics beyond automation capability
   - Provides context when escalating to humans
   - Monitors resolution progress

5. `FeedbackAgent`: Processes customer feedback
   - Analyzes ratings and comments
   - Updates solution success metrics
   - Identifies improvement opportunities
   - Signals knowledge base updates
   - Provides training signals for ML models

6. `ChatbotAgent`: Handles direct user conversations
   - Manages conversation state and flow
   - Provides information and troubleshooting steps
   - Creates tickets when necessary
   - Offers guided support experiences
   - Routes complex issues to appropriate channels

### `ml_models.py`
**Purpose**: Machine learning model implementations.
**Functionality**:
- Defines ML models for various prediction tasks
- Handles model training and inference
- Processes data for machine learning operations

**Key Models**:
1. `TicketClassifier`: Categorizes support tickets
   - Uses TF-IDF vectorization and classification algorithms
   - Learns from historical ticket data
   - Predicts appropriate categories for new tickets
   - Provides confidence scores for predictions

2. `ResolutionPredictor`: Suggests ticket resolutions
   - Matches issues with potential solutions
   - Ranks solutions by predicted effectiveness
   - Learns from historical resolution outcomes
   - Improves suggestions based on feedback

3. `SentimentAnalyzer`: Analyzes customer sentiment
   - Detects emotions in customer messages
   - Provides sentiment scores and categories
   - Suggests appropriate response tones
   - Identifies urgent or frustrated customers

4. `ConversationHealthAnalyzer`: Evaluates conversation quality
   - Analyzes interaction patterns and flow
   - Detects issues in conversation quality
   - Provides metrics on conversation effectiveness
   - Suggests improvements for conversation handling

5. `AdvancedResolutionPredictor`: Enhanced solution generation
   - Combines multiple approaches for solution suggestions
   - Generates follow-up questions for clarification
   - Creates quick-action suggestions
   - Provides context-aware resolution paths

6. `CollaborativeAgentSystem`: Enables multi-agent collaboration
   - Coordinates activities between agents and humans
   - Tracks agent participation in complex issues
   - Manages handoffs between different entities
   - Facilitates knowledge sharing in resolution process

### `data_processing.py`
**Purpose**: Data loading and processing.
**Functionality**:
- Loads initial data for the application
- Processes datasets for ML training
- Prepares data for knowledge base population

**Key Functions**:
1. `load_initial_data()`: Seeds the database with initial content
2. `load_historical_tickets()`: Imports ticket data from CSV files
3. `load_conversation_data()`: Loads conversation examples for training

### `populate_knowledge_base.py`
**Purpose**: Initializes the knowledge base with seed data.
**Functionality**:
- Creates initial knowledge base entries
- Formats structured solutions for common issues
- Seeds the system with expert knowledge

**Process**:
1. Checks if knowledge base already contains entries
2. Creates sample entries for common support categories
3. Properly formats markdown content with problem-solution structure
4. Adds appropriate tags and metadata
5. Commits entries to the database

## Database Management

### `reset_db.py`
**Purpose**: Utility script for database reset.
**Functionality**:
- Drops all tables and recreates them
- Seeds the database with initial data
- Useful for development and testing

## Interface Files

### `templates/` (Directory)
**Purpose**: HTML templates for web interface.
**Key Templates**:
- `layout.html`: Base template with common structure
- `index.html`: Home page
- `dashboard.html`: Admin analytics dashboard
- `tickets.html`: Ticket management interface
- `chat.html`: Chatbot interface
- `knowledge_base.html`: Knowledge repository
- `auth/`: Authentication-related templates (login, register, profile)

### `static/` (Directory)
**Purpose**: Static assets for the web interface.
**Contents**:
- `css/`: Stylesheets including custom CSS
- `js/`: JavaScript files for interactive features
- `img/`: Image assets and icons
- `fonts/`: Custom font files

#### Key JavaScript Files:
- `theme.js`: Handles dark/light mode themes
- `chat.js`: Manages chatbot interactions
- `dashboard.js`: Powers dashboard visualizations
- `tickets.js`: Handles ticket UI functionality
- `knowledge_base.js`: Manages knowledge base interface

## Additional Files

### `Analysis.md`
**Purpose**: Technical analysis of the system architecture.
**Contents**:
- System architecture documentation
- AI/ML component explanations
- Data flow descriptions
- Implementation details
- Technical considerations
- Interview Q&A

## File Interactions and Workflow

### Request Processing Workflow

When a user interaction occurs, the system follows this file interaction sequence:

1. **Request Routing**:
   - `main.py` receives the HTTP request
   - Request is processed by Flask and routed to the appropriate handler in `routes.py`

2. **Data Handling**:
   - `routes.py` extracts data from the request (using `forms.py` for web forms)
   - Data is validated and processed
   - Required database operations are performed via models in `models.py`

3. **AI Processing**:
   - For AI-related operations, the route handler calls appropriate functions in `agents.py`
   - These agents may utilize ML models from `ml_models.py`
   - Utility functions from `utils.py` assist in data formatting and processing

4. **Knowledge Base Integration**:
   - Knowledge base queries use functions from `utils.py`
   - Knowledge entries are retrieved from database via `models.py`
   - Results are processed and returned to the route handler

5. **Response Generation**:
   - The route handler formats the response data
   - For web interfaces, data is passed to a template from the `templates/` directory
   - For API endpoints, data is returned as JSON

### ML Training Workflow

When the system learns from new data:

1. **Data Collection**:
   - User interactions and feedback are collected via endpoints in `routes.py`
   - Data is stored in the database through models in `models.py`

2. **Feedback Processing**:
   - `FeedbackAgent` in `agents.py` processes user feedback
   - Success metrics are updated in the database

3. **Model Retraining**:
   - Periodically, models in `ml_models.py` retrain using updated data
   - New patterns and correlations are learned

4. **Knowledge Base Updates**:
   - Successful resolutions create new knowledge base entries
   - `utils.py` functions transform ticket data into knowledge entries

## Conclusion

The project follows a modular architecture where each file has a specific purpose and clear interactions with other components. This design facilitates:

1. **Separation of Concerns**: Each file handles distinct functionality
2. **Maintainability**: Changes to one component have minimal impact on others
3. **Extensibility**: New features can be added by extending existing patterns
4. **Testability**: Components can be tested in isolation

The AI/ML functionality is seamlessly integrated through the agent system, allowing the application to provide intelligent support features while maintaining a clean architecture.
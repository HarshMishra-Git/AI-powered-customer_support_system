# AI-powered Customer Support System

## Overview
This repository contains an AI-powered customer support system designed to provide technical support, create tickets, and offer solutions for common problems. The system uses machine learning models to classify tickets, predict resolutions, analyze sentiments, and handle conversations with users.

## Features
- **Ticket Classification**: Classifies support tickets into predefined categories.
- **Sentiment Analysis**: Analyzes the sentiment of customer messages.
- **Resolution Prediction**: Suggests solutions for support tickets based on historical data.
- **Conversation Management**: Handles user queries with structured conversation flow.
- **Knowledge Base**: Automatically creates knowledge base entries from resolved tickets.
- **Gamification**: Includes user roles, badges, and experience points for enhanced engagement.

## Repository Structure
```
AI-powered-customer_support_system/
│
├── agents.py               # Contains agent classes for ticket classification, resolution, escalation, feedback, and chatbot interactions.
├── app.py                  # Initializes Flask application and sets up database configurations.
├── forms.py                # Defines form classes for user login, registration, and profile update.
├── main.py                 # Entry point for the Flask application.
├── models.py               # Defines database models for users, tickets, solutions, feedback, teams, etc.
├── routes.py               # Defines routes and API endpoints for the application.
├── utils.py                # Utility functions for ticket ID generation, error code extraction, and more.
├── ml_models.py            # Machine learning models for ticket classification, resolution prediction, sentiment analysis, and conversation health analysis.
├── requirements.txt        # List of dependencies required for the project.
├── Dockerfile              # Dockerfile for containerizing the application.
└── Procfile                # Procfile for specifying the command to run the application (for Heroku deployment).
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Pip (Python package installer)
- Git (for cloning the repository)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/HarshMishra-Git/AI-powered-customer_support_system.git
   cd AI-powered-customer_support_system
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add the following variables:
   ```env
   FLASK_APP=main.py
   FLASK_ENV=development
   SESSION_SECRET=your_secret_key
   DATABASE_URL=sqlite:///instance/support_system.db
   ```

5. **Initialize the database**:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

### Running the Application

1. **Start the Flask application**:
   ```bash
   flask run
   ```

2. **Access the application**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

### Deployment

#### Deploy to Heroku

1. **Install Heroku CLI**:
   [Heroku CLI Installation Guide](https://devcenter.heroku.com/articles/heroku-cli#download-and-install)

2. **Create a new Heroku app**:
   ```bash
   heroku create
   ```

3. **Deploy to Heroku**:
   ```bash
   git push heroku main
   ```

4. **Set environment variables on Heroku**:
   ```bash
   heroku config:set SESSION_SECRET=your_secret_key
   heroku config:set DATABASE_URL=your_database_url
   ```

5. **Open the application**:
   ```bash
   heroku open
   ```

#### Deploy to Render

1. **Sign up for Render**:
   [Render Sign Up](https://render.com/)

2. **Create a new web service**:
   - Connect your GitHub repository.
   - Specify the build and run commands:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn main:app`

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For any inquiries or support, please contact Harsh Mishra at [your_email@example.com].

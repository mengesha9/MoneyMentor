# MoneyMentor Backend API

AI-powered financial education chatbot with quiz engine and calculation services. This is a pure backend API implementation using FastAPI with CrewAI agents for intelligent orchestration.

## Features

- **AI-Powered Chat**: Conversational financial education using GPT-4 models
- **Quiz Engine**: Diagnostic and micro-quizzes with intelligent triggering
- **Financial Calculations**: Debt payoff, savings goals, and loan amortization
- **Content Management**: PDF/document ingestion with vector search
- **Progress Tracking**: User learning analytics and progress monitoring
- **Session Management**: Stateful conversations with Redis caching
- **Google Sheets Integration**: Export user profiles and analytics data to Google Sheets

## Architecture

- **FastAPI**: Modern Python web framework for APIs
- **CrewAI**: Multi-agent orchestration for intelligent decision-making
- **LangChain**: LLM integration and document processing
- **Supabase**: Vector database for content storage and search
- **Redis**: Session management and caching
- **OpenAI**: GPT-4 and GPT-4-mini for AI responses

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment variables:
   ```bash
   cp env.example .env
   ```
5. Configure your `.env` file with required API keys and settings

## Environment Variables

Required environment variables (see `env.example`):

- `OPENAI_API_KEY`: OpenAI API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `GOOGLE_SHEETS_CREDENTIALS_FILE`: Path to Google Sheets credentials JSON
- `GOOGLE_SHEETS_SPREADSHEET_ID`: Google Sheets ID for progress tracking
- `SECRET_KEY`: JWT secret key
- `REDIS_URL`: Redis connection URL

## Running the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Chat API (`/api/chat`)

- `POST /api/chat/message` - Send a chat message
- `POST /api/chat/start-diagnostic` - Start diagnostic quiz
- `GET /api/chat/session/{user_id}` - Get session information
- `POST /api/chat/calculate` - Perform financial calculations

### Quiz API (`/api/quiz`)

- `POST /api/quiz/generate` - Generate a quiz
- `POST /api/quiz/submit` - Submit quiz answer
- `GET /api/quiz/history/{user_id}` - Get quiz history

### Calculation API (`/api/calculation`)

- `POST /api/calculation/debt-payoff` - Calculate debt payoff plan
- `POST /api/calculation/savings-goal` - Calculate savings goal plan
- `POST /api/calculation/loan-amortization` - Calculate loan amortization
- `POST /api/calculation/custom` - Custom financial calculations

### Progress API (`/api/progress`)

- `GET /api/progress/user/{user_id}` - Get user progress
- `GET /api/progress/analytics/{user_id}` - Get learning analytics
- `GET /api/progress/leaderboard` - Get leaderboard
- `POST /api/progress/export/{user_id}` - Export specific user data to Google Sheets
- `POST /api/progress/export-all-users` - Export all user profiles to Google Sheets UserProfiles tab

## Google Sheets Integration

The backend includes comprehensive Google Sheets integration for exporting user analytics and profile data. The system creates and maintains several tabs:

### Available Tabs

1. **UserProfiles**: Single table with user profile data
   - Columns: `first_name`, `last_name`, `email`, `total_chats`, `quizzes_taken`, `day_streak`, `days_active`
   - Purpose: Overview of all users and their engagement metrics

2. **QuizResponses**: Detailed quiz response tracking
   - Columns: `user_id`, `timestamp`, `quiz_id`, `topic_tag`, `selected_option`, `correct`, `session_id`

3. **EngagementLogs**: User engagement analytics
   - Columns: `user_id`, `session_id`, `messages_per_session`, `session_duration`, `quizzes_attempted`, `pretest_completed`, `last_activity`, `confidence_rating`

4. **ChatLogs**: Chat message history
   - Columns: `user_id`, `session_id`, `timestamp`, `message_type`, `message`, `response`

5. **CourseProgress**: Course completion tracking
   - Columns: `user_id`, `session_id`, `course_id`, `course_name`, `page_number`, `total_pages`, `completed`, `timestamp`

### Setup

1. Create a Google Sheets spreadsheet
2. Set up Google Sheets API credentials
3. Configure environment variables:
   - `GOOGLE_SHEET_ID`: Your Google Sheets spreadsheet ID
   - `GOOGLE_CLIENT_EMAIL`: Email to share the sheet with (read-only access)
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your service account JSON file

### Usage

#### Manual Export
```bash
# Export all user profiles to Google Sheets
curl -X POST "http://localhost:8000/api/progress/export-all-users"

# Export specific user profile
curl -X POST "http://localhost:8000/api/progress/export/{user_id}"
```

#### Automatic Synchronization
The system automatically syncs user profiles to Google Sheets in the following scenarios:

1. **Background Sync Service**: Runs every 5 minutes to ensure data is always up-to-date
2. **Real-time Updates**: When user profiles are updated through the application layer
3. **Database Notifications**: Real-time notifications when database triggers update user profiles
4. **Database Triggers**: When users take quizzes or send chat messages (triggers database functions)

#### Sync Status and Control
```bash
# Check sync service status
curl -X GET "http://localhost:8000/sync/status"

# Check Supabase listener status
curl -X GET "http://localhost:8000/sync/supabase-listener"

# Force an immediate sync
curl -X POST "http://localhost:8000/sync/force"
```

#### Supabase Real-time Notification System

The system uses Supabase's real-time subscriptions to listen for changes to the `user_profiles` table. This ensures that Google Sheets stays synchronized even when updates happen at the database level.

**How it works:**
1. The `SupabaseListenerService` subscribes to INSERT and UPDATE events on the `user_profiles` table
2. When a user profile is updated (by database triggers or direct updates), Supabase sends a real-time notification
3. The listener receives the notification and triggers a Google Sheets sync after a 30-second delay (to batch multiple rapid updates)
4. The background sync service also runs every 5 minutes as a fallback

#### Testing
```bash
# Test automatic synchronization
python test_automatic_sync.py

# Test sync frequency
python test_automatic_sync.py --frequency

# Test Supabase real-time notification system
python test_supabase_notifications.py

# Test only notification callbacks
python test_supabase_notifications.py --callbacks-only
```

## Usage Examples

### Send a Chat Message

```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I start investing?",
    "user_id": "user123"
  }'
```

### Generate a Quiz

```bash
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "quiz_type": "micro",
    "topic": "investing basics"
  }'
```

### Calculate Debt Payoff

```bash
curl -X POST "http://localhost:8000/api/calculation/debt-payoff" \
  -H "Content-Type: application/json" \
  -d '{
    "calculation_type": "payoff",
    "principal": 5000,
    "interest_rate": 18.5,
    "monthly_payment": 200
  }'
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
flake8 .
```

## Deployment

The API is designed to be deployed as a containerized service. Key considerations:

1. Set up environment variables in your deployment environment
2. Configure Redis and Supabase connections
3. Set up Google Sheets API credentials
4. Configure CORS origins for your frontend domains

## License

This project is proprietary software developed for MoneyMentor. 
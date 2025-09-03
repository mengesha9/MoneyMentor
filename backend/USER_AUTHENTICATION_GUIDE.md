# MoneyMentor User Authentication System

This guide covers the complete user authentication and profile management system for MoneyMentor.

## Features

### 🔐 Authentication
- **User Registration**: Create new accounts with email and password
- **User Login**: Secure login with JWT tokens
- **Password Management**: Change password and reset functionality
- **Account Deletion**: Secure account deletion with password confirmation

### 👤 Profile Management
- **Profile Information**: First name, last name, email management
- **Statistics Tracking**: 
  - Total Chats
  - Quizzes Taken
  - Day Streak
  - Days Active
- **Activity Summary**: Detailed activity tracking over time
- **Leaderboard**: Compare performance with other users

### 🛡️ Security Features
- **Password Hashing**: Bcrypt encryption for passwords
- **JWT Tokens**: Secure access tokens with expiration
- **Input Validation**: Comprehensive validation for all inputs
- **Error Handling**: Secure error responses without information leakage

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
```

### User Profiles Table
```sql
CREATE TABLE user_profiles (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    total_chats INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    day_streak INTEGER DEFAULT 0,
    days_active INTEGER DEFAULT 0,
    last_activity_date DATE DEFAULT CURRENT_DATE,
    streak_start_date DATE DEFAULT CURRENT_DATE,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    UNIQUE(user_id)
);
```

## API Endpoints

### Authentication Endpoints

#### POST `/api/user/register`
Register a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "is_verified": false,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "profile": {
        "user_id": "uuid",
        "total_chats": 0,
        "quizzes_taken": 0,
        "day_streak": 0,
        "days_active": 0,
        "last_activity_date": "2024-01-01",
        "streak_start_date": "2024-01-01",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

#### POST `/api/user/login`
Login with email and password.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response:** Same as register endpoint.

### Profile Management Endpoints

#### GET `/api/user/profile`
Get current user's profile and statistics (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "is_verified": false,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    },
    "profile": {
        "user_id": "uuid",
        "total_chats": 15,
        "quizzes_taken": 8,
        "day_streak": 5,
        "days_active": 12,
        "last_activity_date": "2024-01-15",
        "streak_start_date": "2024-01-11",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z"
    },
    "statistics": {
        "profile": {...},
        "statistics": {
            "total_chat_messages": 45,
            "total_quiz_responses": 24,
            "quiz_accuracy": 87.5,
            "correct_answers": 21,
            "total_answers": 24
        }
    }
}
```

#### PUT `/api/user/profile`
Update user profile information (requires authentication).

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com"
}
```

#### PUT `/api/user/password`
Change user password (requires authentication).

**Request Body:**
```json
{
    "current_password": "oldpassword123",
    "new_password": "newpassword456"
}
```

#### DELETE `/api/user/account`
Delete user account (requires authentication).

**Request Body:**
```json
{
    "current_password": "userpassword123",
    "new_password": "userpassword123"
}
```

### Activity and Statistics Endpoints

#### GET `/api/user/activity`
Get user activity summary for the last N days (requires authentication).

**Query Parameters:**
- `days` (optional): Number of days (1-365, default: 30)

**Response:**
```json
{
    "period_days": 30,
    "start_date": "2023-12-16",
    "end_date": "2024-01-15",
    "activity_by_day": {
        "2024-01-15": {
            "chats": 3,
            "quizzes": 2,
            "correct_answers": 1,
            "total_answers": 2
        },
        "2024-01-14": {
            "chats": 1,
            "quizzes": 0,
            "correct_answers": 0,
            "total_answers": 0
        }
    }
}
```

#### GET `/api/user/leaderboard`
Get leaderboard data for top users.

**Query Parameters:**
- `limit` (optional): Number of users to return (1-100, default: 10)

**Response:**
```json
{
    "leaderboard": [
        {
            "rank": 1,
            "user_id": "uuid",
            "name": "John Doe",
            "day_streak": 15,
            "days_active": 25,
            "total_chats": 45,
            "quizzes_taken": 20
        }
    ],
    "total_users": 10
}
```

### Utility Endpoints

#### GET `/api/user/me`
Get current user information (requires authentication).

#### POST `/api/user/password/reset`
Request password reset (sends email).

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

#### POST `/api/user/password/reset/confirm`
Confirm password reset with token.

**Request Body:**
```json
{
    "token": "reset_token_here",
    "new_password": "newpassword456"
}
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Add these to your `.env` file:
```env
# Authentication
SECRET_KEY=your-super-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Supabase (existing)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-service-key
```

### 3. Run Database Migrations
```bash
python run_migrations.py
```

This will:
- Create all necessary database tables
- Set up indexes for performance
- Create triggers for automatic activity tracking
- Create a test user for development

### 4. Start the Server
```bash
uvicorn app.main:app --reload
```

### 5. Test the API
Visit `http://localhost:8000/docs` to see the interactive API documentation.

## Usage Examples

### Frontend Integration

#### Login Flow
```javascript
// Login user
const loginResponse = await fetch('/api/user/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});

const { access_token, user, profile } = await loginResponse.json();

// Store token
localStorage.setItem('access_token', access_token);

// Use token for authenticated requests
const profileResponse = await fetch('/api/user/profile', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});
```

#### Profile Management
```javascript
// Update profile
const updateResponse = await fetch('/api/user/profile', {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        first_name: 'John',
        last_name: 'Smith'
    })
});

// Get activity summary
const activityResponse = await fetch('/api/user/activity?days=7', {
    headers: {
        'Authorization': `Bearer ${access_token}`
    }
});
```

### Backend Integration

#### User Service Usage
```python
from app.services.user_service import UserService
from app.core.auth import get_current_active_user

# In your FastAPI endpoint
@router.post("/some-endpoint")
async def some_endpoint(
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    # Increment chat count
    await user_service.increment_chat_count(current_user["id"])
    
    # Get user statistics
    stats = await user_service.get_user_statistics(current_user["id"])
    
    return {"message": "Success", "stats": stats}
```

## Security Considerations

### Password Security
- Passwords are hashed using bcrypt
- Minimum password length: 8 characters
- Passwords are never stored in plain text

### Token Security
- JWT tokens expire after 30 minutes (configurable)
- Tokens are signed with a secret key
- Tokens contain user ID for authentication

### Input Validation
- All inputs are validated using Pydantic models
- Email addresses are validated for format
- SQL injection is prevented through parameterized queries

### Error Handling
- Generic error messages to prevent information leakage
- Detailed logging for debugging
- Proper HTTP status codes

## Development

### Test User
For development, a test user is automatically created:
- **Email**: `test@example.com`
- **Password**: `testpassword123`

### Testing Endpoints
1. Register a new user: `POST /api/user/register`
2. Login: `POST /api/user/login`
3. Get profile: `GET /api/user/profile`
4. Update profile: `PUT /api/user/profile`
5. Get activity: `GET /api/user/activity`
6. Get leaderboard: `GET /api/user/leaderboard`

### Database Triggers
The system includes automatic triggers that:
- Update user activity when chat messages are sent
- Update user activity when quiz responses are submitted
- Maintain day streaks automatically
- Track total days active

## Troubleshooting

### Common Issues

1. **Migration fails**: Check Supabase connection and permissions
2. **Authentication fails**: Verify SECRET_KEY is set
3. **Profile not found**: Run migrations to create tables
4. **Token expired**: Implement token refresh logic

### Debug Mode
Set `DEBUG=true` in your `.env` file for detailed error messages.

### Logs
Check the application logs for detailed error information:
```bash
uvicorn app.main:app --reload --log-level debug
```

## Future Enhancements

- [ ] Email verification system
- [ ] Social login (Google, Facebook)
- [ ] Two-factor authentication
- [ ] Password reset email functionality
- [ ] User roles and permissions
- [ ] Account recovery options
- [ ] Session management
- [ ] Rate limiting
- [ ] Audit logging 
# Course Statistics Feature Guide

## Overview

The Course Statistics feature allows you to track detailed progress for each user across multiple courses. This includes:

- **Course Name**: The name of the course
- **Total Questions Taken**: Number of questions attempted
- **Score**: Percentage score achieved
- **Tabs Completed**: Number of course sections/tabs completed
- **Level**: Difficulty level (easy, medium, hard)

## Database Schema

### New Column Added

The `user_profiles` table now includes a new JSONB column:

```sql
ALTER TABLE public.user_profiles 
ADD COLUMN course_statistics JSONB DEFAULT '[]'::jsonb;
```

### Data Structure

Each user can have multiple course statistics stored as an array of objects:

```json
[
  {
    "course_name": "Budgeting and Saving",
    "total_questions_taken": 15,
    "score": 85,
    "tabs_completed": 3,
    "level": "medium"
  },
  {
    "course_name": "Money, Goals and Mindset",
    "total_questions_taken": 10,
    "score": 92,
    "tabs_completed": 2,
    "level": "easy"
  }
]
```

## API Endpoints

### 1. Add Course Statistics

**POST** `/api/course-statistics/course-statistics`

Add or update course statistics for the current user.

**Request Body:**
```json
{
  "course_name": "Budgeting and Saving",
  "total_questions_taken": 15,
  "score": 85,
  "tabs_completed": 3,
  "level": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Course statistics updated for Budgeting and Saving",
  "data": {
    "course_name": "Budgeting and Saving",
    "total_questions_taken": 15,
    "score": 85,
    "tabs_completed": 3,
    "level": "medium"
  }
}
```

### 2. Update Course Progress

**PUT** `/api/course-statistics/course-progress`

Update specific aspects of course progress.

**Request Body:**
```json
{
  "course_name": "Budgeting and Saving",
  "questions_taken": 5,
  "score": 90,
  "tabs_completed": 4,
  "level": "hard"
}
```

### 3. Get Course Statistics

**GET** `/api/course-statistics/course-statistics?course_name=optional`

Get course statistics for the current user.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "course_name": "Budgeting and Saving",
      "total_questions_taken": 20,
      "score": 90,
      "tabs_completed": 4,
      "level": "hard"
    }
  ],
  "count": 1
}
```

## Google Sheets Integration

### New Columns in UserProfiles Tab

The Google Sheets export now includes additional columns:

| Column | Description |
|--------|-------------|
| `courses_enrolled` | Number of courses the user is enrolled in |
| `total_course_score` | Sum of all course scores |
| `courses_completed` | Number of courses with completed tabs |
| `course_details` | Detailed summary of all courses |

### Example Google Sheets Data

```
first_name | last_name | email | total_chats | quizzes_taken | day_streak | days_active | courses_enrolled | total_course_score | courses_completed | course_details
John       | Doe       | john@example.com | 25 | 10 | 5 | 7 | 2 | 177 | 2 | Budgeting and Saving: 90% (4 tabs, 20 questions, hard) | Money, Goals and Mindset: 87% (2 tabs, 10 questions, easy)
```

## Usage Examples

### 1. Adding Course Statistics

```python
from app.services.user_service import UserService

user_service = UserService()

# Add course statistics
course_stats = {
    "course_name": "Budgeting and Saving",
    "total_questions_taken": 15,
    "score": 85,
    "tabs_completed": 3,
    "level": "medium"
}

success = await user_service.add_course_statistics(user_id, course_stats)
```

### 2. Updating Course Progress

```python
# Update specific aspects
success = await user_service.update_course_progress(
    user_id=user_id,
    course_name="Budgeting and Saving",
    questions_taken=5,  # Add 5 more questions
    score=90,           # Update score to 90%
    tabs_completed=4    # Update tabs completed
)
```

### 3. Getting Course Statistics

```python
# Get all course statistics
all_stats = await user_service.get_course_statistics(user_id)

# Get specific course statistics
course_stats = await user_service.get_course_statistics(
    user_id, 
    course_name="Budgeting and Saving"
)
```

## Migration

### Running the Migration

1. **Automatic Migration**: The migration runs automatically when you start the application.

2. **Manual Migration**: Run the migration script:
   ```bash
   python3 run_course_statistics_migration.py
   ```

### Migration SQL

```sql
-- Add the course_statistics column as JSONB
ALTER TABLE public.user_profiles 
ADD COLUMN IF NOT EXISTS course_statistics JSONB DEFAULT '[]'::jsonb;

-- Add an index for better query performance on the JSONB column
CREATE INDEX IF NOT EXISTS idx_user_profiles_course_statistics 
ON public.user_profiles USING GIN (course_statistics);

-- Add a comment to document the structure
COMMENT ON COLUMN public.user_profiles.course_statistics IS 
'Array of course statistics objects. Each object contains: {
  "course_name": "string",
  "total_questions_taken": number,
  "score": number,
  "tabs_completed": number,
  "level": "easy" | "medium" | "hard"
}';
```

## Testing

### Run the Test Script

```bash
python3 test_course_statistics.py
```

This will test:
1. Adding course statistics
2. Updating course progress
3. Retrieving course statistics
4. Google Sheets export formatting
5. Integration with the export system

## Integration Points

### Frontend Integration

The frontend can call these endpoints to:

1. **Track Quiz Progress**: Update course statistics when users complete quizzes
2. **Track Course Progress**: Update tabs completed as users navigate through courses
3. **Display Progress**: Show users their progress across all courses
4. **Analytics Dashboard**: Display comprehensive course statistics

### Backend Integration

The course statistics are automatically:

1. **Synced to Google Sheets**: Via the background sync service
2. **Included in User Profiles**: When retrieving user data
3. **Logged for Analytics**: For tracking user engagement

## Best Practices

### 1. Data Validation

- Always validate the `level` field (must be 'easy', 'medium', or 'hard')
- Ensure `score` is between 0 and 100
- Validate that `tabs_completed` is a positive integer

### 2. Performance

- The JSONB column is indexed for efficient queries
- Use the `update_course_progress` method for incremental updates
- Batch updates when possible

### 3. Error Handling

- Always check the return value of course statistics methods
- Handle cases where course statistics don't exist
- Log errors for debugging

### 4. Google Sheets Export

- Course details are formatted as readable strings
- Long course details may be truncated in Google Sheets
- Consider the column width when viewing in Google Sheets

## Troubleshooting

### Common Issues

1. **Migration Fails**: Ensure you have proper database permissions
2. **Invalid Level**: Only 'easy', 'medium', 'hard' are valid levels
3. **Google Sheets Export Issues**: Check the Google Sheets service configuration
4. **Performance Issues**: Ensure the JSONB index is created

### Debug Commands

```bash
# Check if migration ran successfully
python3 run_course_statistics_migration.py

# Test the functionality
python3 test_course_statistics.py

# Check Google Sheets export
python3 debug_google_sheets.py
```

## Future Enhancements

1. **Course Categories**: Add support for course categories/tags
2. **Time Tracking**: Track time spent on each course
3. **Achievement System**: Add badges/achievements based on course completion
4. **Advanced Analytics**: More detailed progress tracking and reporting
5. **Course Recommendations**: Suggest courses based on user progress

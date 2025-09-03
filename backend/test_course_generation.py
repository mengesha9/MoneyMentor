#!/usr/bin/env python3
"""
Test script for the course generation endpoint
This simulates what the frontend would send to generate a course
"""

import asyncio
import httpx
import json
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = "/api/quiz/submit"

# Dummy data that matches the frontend request format
def create_dummy_quiz_submission():
    """Create dummy quiz submission data that matches QuizSubmissionBatch schema"""
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Create dummy quiz responses for a diagnostic quiz
    quiz_responses = [
        {
            "quiz_id": f"quiz_{session_id}_1",
            "selected_option": "B",
            "correct": True,
            "topic": "Investing"
        },
        {
            "quiz_id": f"quiz_{session_id}_2", 
            "selected_option": "A",
            "correct": False,
            "topic": "Budgeting"
        },
        {
            "quiz_id": f"quiz_{session_id}_3",
            "selected_option": "C", 
            "correct": True,
            "topic": "Saving"
        },
        {
            "quiz_id": f"quiz_{session_id}_4",
            "selected_option": "D",
            "correct": False,
            "topic": "Debt Management"
        },
        {
            "quiz_id": f"quiz_{session_id}_5",
            "selected_option": "B",
            "correct": True,
            "topic": "Investing"
        }
    ]
    
    # Create the full request payload
    payload = {
        "quiz_type": "diagnostic",  # This triggers course generation
        "session_id": session_id,
        "responses": quiz_responses,
        "selected_course_type": "investing-basics"  # Optional: specific course type
    }
    
    return payload, session_id

async def test_course_generation():
    """Test the course generation endpoint"""
    
    print("🚀 Testing Course Generation Endpoint")
    print("=" * 60)
    
    # Create dummy data
    payload, session_id = create_dummy_quiz_submission()
    
    print(f"📋 Test Data:")
    print(f"  Session ID: {session_id}")
    print(f"  Quiz Type: {payload['quiz_type']}")
    print(f"  Number of Responses: {len(payload['responses'])}")
    print(f"  Selected Course Type: {payload['selected_course_type']}")
    print()
    
    print("📝 Request Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        # Make the request
        async with httpx.AsyncClient() as client:
            print("🌐 Making request to course generation endpoint...")
            print(f"URL: {BASE_URL}{API_ENDPOINT}")
            print()
            
            # Note: This endpoint requires authentication, so we'll get a 401
            # In a real test, you'd need to include an Authorization header
            response = await client.post(
                f"{BASE_URL}{API_ENDPOINT}",
                json=payload,
                timeout=30.0
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            print()
            
            if response.status_code == 401:
                print("🔒 Authentication required (expected for protected endpoint)")
                print("To test with authentication, you need to:")
                print("1. Login to get a JWT token")
                print("2. Include Authorization: Bearer <token> header")
                print()
                
                # Show what the response would look like if authenticated
                print("📋 Expected Response Format (if authenticated):")
                expected_response = {
                    "success": True,
                    "data": {
                        "user_id": "user_uuid",
                        "quiz_type": "diagnostic",
                        "overall_score": 60.0,
                        "topic_breakdown": {
                            "Investing": {"correct": 2, "total": 2, "percentage": 100.0},
                            "Budgeting": {"correct": 0, "total": 1, "percentage": 0.0},
                            "Saving": {"correct": 1, "total": 1, "percentage": 100.0},
                            "Debt Management": {"correct": 0, "total": 1, "percentage": 0.0}
                        },
                        "recommended_course_id": "course_uuid",
                        "course_generation_status": "completed",
                        "generated_course": {
                            "title": "Personalized Investing Basics Course",
                            "pages": 10,
                            "course_level": "intermediate"
                        }
                    }
                }
                print(json.dumps(expected_response, indent=2))
                
            elif response.status_code == 200:
                print("✅ Success! Course generated successfully")
                print("📄 Response Body:")
                print(json.dumps(response.json(), indent=2))
                
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                print("📄 Response Body:")
                try:
                    print(json.dumps(response.json(), indent=2))
                except:
                    print(response.text)
                    
    except httpx.ConnectError:
        print("❌ Connection Error: Could not connect to the server")
        print(f"Make sure the backend is running at {BASE_URL}")
        print("Start the backend with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        
    except httpx.TimeoutException:
        print("❌ Timeout Error: Request took too long")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Error Type: {type(e).__name__}")

def test_without_server():
    """Test the data structure without making HTTP requests"""
    print("🧪 Testing Data Structure (No Server Required)")
    print("=" * 60)
    
    payload, session_id = create_dummy_quiz_submission()
    
    print("📋 Generated Test Data:")
    print(f"Session ID: {session_id}")
    print(f"Quiz Type: {payload['quiz_type']}")
    print(f"Number of Responses: {len(payload['responses'])}")
    print()
    
    print("📝 Full Request Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    print("🔍 Data Validation:")
    
    # Validate quiz responses
    for i, response in enumerate(payload['responses']):
        print(f"  Response {i+1}:")
        required_fields = ['quiz_id', 'selected_option', 'correct', 'topic']
        for field in required_fields:
            if field in response:
                print(f"    ✅ {field}: {response[field]}")
            else:
                print(f"    ❌ Missing {field}")
        
        # Validate selected_option format
        selected = response.get('selected_option')
        if selected in ['A', 'B', 'C', 'D']:
            print(f"    ✅ selected_option format: {selected}")
        else:
            print(f"    ❌ Invalid selected_option: {selected}")
    
    print()
    print("📚 Expected Course Generation:")
    print("  - This diagnostic quiz will trigger AI course generation")
    print("  - Course will be personalized based on quiz performance")
    print("  - 10 pages of content will be generated")
    print("  - Course level determined by overall score")
    print("  - Focus topic derived from quiz responses")

if __name__ == "__main__":
    print("🎯 Course Generation Endpoint Test")
    print("=" * 60)
    print()
    
    # First test the data structure
    test_without_server()
    print()
    print("=" * 60)
    print()
    
    # Then test the actual endpoint (if server is running)
    try:
        asyncio.run(test_course_generation())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}") 
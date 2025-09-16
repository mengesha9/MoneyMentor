# Enhanced Background Sync Service

## Overview

The MoneyMentor backend now includes a robust, non-blocking background sync service that automatically syncs user data to Google Sheets at configurable intervals. This service is designed for production use with comprehensive error handling, health monitoring, and graceful shutdown capabilities.

## Key Features

### 🚀 **Non-Blocking Operation**
- Runs asynchronously without blocking user requests
- Automatically pauses during high-traffic periods
- Uses cooperative multitasking for optimal performance

### ⚙️ **Configurable Settings**
- Sync interval (default: 5 minutes)
- Retry logic with exponential backoff
- Enable/disable specific sync operations
- Health monitoring intervals

### 🏥 **Health Monitoring**
- Real-time health status tracking
- Automatic failure recovery
- Comprehensive metrics and statistics
- Alert thresholds for consecutive failures

### 🔧 **Error Handling & Recovery**
- Automatic retry with exponential backoff
- Circuit breaker pattern for API failures
- Graceful degradation when services are unavailable
- Detailed error logging and tracking

### 📊 **Comprehensive Metrics**
- Success/failure rates
- Average sync duration
- Uptime tracking
- Consecutive failure monitoring

## Configuration

### Environment Variables

```bash
# Sync Intervals
SYNC_INTERVAL_SECONDS=300                    # 5 minutes (default)
SYNC_HEALTH_CHECK_INTERVAL=60               # 1 minute (default)

# Retry Configuration
SYNC_MAX_RETRIES=3                          # Max retry attempts (default)
SYNC_RETRY_DELAY_SECONDS=5                  # Base retry delay (default)
SYNC_MAX_CONSECUTIVE_FAILURES=5             # Circuit breaker threshold (default)

# Feature Toggles
SYNC_ENABLE_COURSE_STATS=true               # Enable course statistics sync (default)
SYNC_ENABLE_USER_PROFILES=true              # Enable user profiles sync (default)
```

### Programmatic Configuration

```python
from app.services.background_sync_service import BackgroundSyncService, SyncConfig

# Custom configuration
config = SyncConfig(
    interval_seconds=600,      # 10 minutes
    max_retries=5,            # 5 retries
    enable_course_stats=True,
    enable_user_profiles=True
)

service = BackgroundSyncService(config)
```

## Automatic Startup

The service starts automatically when the FastAPI application starts, thanks to lifespan events:

```python
# In main.py - handled automatically
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Services start automatically
    await background_sync_service.start_background_sync()

    yield

    # Shutdown: Services stop gracefully
    await background_sync_service.stop_background_sync()
```

## API Endpoints

### Get Sync Status
```http
GET /sync/status
```

**Response:**
```json
{
  "is_running": true,
  "sync_in_progress": false,
  "sync_enabled": true,
  "paused_for_requests": false,
  "last_sync_time": "2025-09-13T17:30:00",
  "next_sync_in_seconds": 245,
  "config": {
    "interval_seconds": 300,
    "max_retries": 3,
    "enable_course_stats": true,
    "enable_user_profiles": true,
    "health_check_interval": 60,
    "max_consecutive_failures": 5
  },
  "statistics": {
    "total_syncs": 15,
    "successful_syncs": 14,
    "failed_syncs": 1,
    "success_rate_percent": 93.33,
    "last_sync_duration_seconds": 2.34,
    "average_sync_duration_seconds": 2.1,
    "consecutive_failures": 0,
    "last_error": null,
    "last_error_time": null,
    "health_status": "healthy",
    "uptime_seconds": 4500,
    "last_health_check": "2025-09-13T17:35:00"
  }
}
```

### Force Immediate Sync
```http
POST /sync/force
```

### Control Sync Service
```http
POST /sync/disable   # Disable sync
POST /sync/enable    # Enable sync
```

## Sync Operations

### User Profiles Sync
- **Source**: Database user profiles table
- **Destination**: `UserProfiles` tab in Google Sheets
- **Data**: Basic user info, engagement metrics, course progress
- **Trigger**: Automatic background sync + real-time updates

### Course Statistics Sync
- **Source**: Calculated course statistics
- **Destination**: `course_statistics` tab in Google Sheets
- **Data**: Course completion, scores, progress tracking
- **Trigger**: Automatic background sync

## Health Monitoring

### Health Status Levels
- **healthy**: Service operating normally
- **warning**: Some failures but within acceptable limits
- **degraded**: Multiple consecutive failures, reduced functionality
- **unhealthy**: Service initialization failed
- **stopped**: Service has been stopped

### Automatic Recovery
- **Circuit Breaker**: Pauses sync after max consecutive failures
- **Exponential Backoff**: Increases delay between retry attempts
- **Auto-Reset**: Resets failure counter after successful sync

## Request Prioritization

The service automatically pauses during user requests to ensure optimal response times:

```python
# Middleware automatically handles this
class RequestPriorityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Pause background sync during requests
        background_sync_service.pause_for_requests()

        response = await call_next(request)

        # Resume after request completes
        background_sync_service.resume_after_requests()

        return response
```

## Logging

### Log Levels
- **INFO**: Normal operations, sync completions
- **WARNING**: Retries, temporary failures
- **ERROR**: Critical failures, service issues

### Sample Logs
```
🚀 Starting enhanced background sync service...
📊 Sync interval: 300 seconds
🔄 Max retries: 3
🏥 Health check interval: 60 seconds
✅ Google Sheets service initialized successfully
🔄 Starting sync loop...
🏥 Health Check - Status: healthy | Uptime: 3600s | Total: 12 | Success: 11 | Failed: 1 | Success Rate: 91.7%
✅ Background sync successful: 90 user profiles synced in 2.34s
```

## Testing

### Quick Test
```bash
# Test the enhanced service
python test_enhanced_sync.py
```

### Integration Test
```bash
# Test with existing data
python test_sync_status.py
```

### Health Check
```bash
# Check service status via API
curl http://localhost:8000/sync/status
```

## Production Deployment

### Best Practices
1. **Monitor Health**: Set up alerts for health status changes
2. **Configure Timeouts**: Adjust intervals based on data volume
3. **Resource Limits**: Monitor memory and CPU usage
4. **Backup Strategy**: Regular Google Sheets backups
5. **Rate Limiting**: Respect Google Sheets API quotas

### Scaling Considerations
- **Large Datasets**: Consider batching for >1000 users
- **High Frequency**: Reduce sync intervals for real-time needs
- **Multiple Instances**: Use distributed locks for multi-instance deployments

## Troubleshooting

### Common Issues

**Service Not Starting**
```bash
# Check environment variables
python -c "import os; print(os.getenv('GOOGLE_SHEET_ID'))"

# Check Google Sheets credentials
python debug_google_sheets.py
```

**High Failure Rate**
```bash
# Check API quotas
# Verify network connectivity
# Review Google Sheets permissions
```

**Slow Sync Performance**
```bash
# Increase sync intervals
# Optimize database queries
# Check network latency
```

### Debug Commands
```bash
# Force sync for testing
curl -X POST http://localhost:8000/sync/force

# Check detailed status
curl http://localhost:8000/sync/status

# View service logs
tail -f logs/moneymentor.log | grep sync
```

## Architecture Benefits

### ✅ **Non-Blocking**
- User requests never wait for sync operations
- Automatic prioritization during peak times
- Cooperative multitasking prevents resource contention

### ✅ **Reliable**
- Comprehensive error handling and recovery
- Health monitoring with automatic alerts
- Circuit breaker pattern prevents cascade failures

### ✅ **Observable**
- Detailed metrics and statistics
- Structured logging for debugging
- Real-time health status monitoring

### ✅ **Maintainable**
- Configuration-driven behavior
- Modular design for easy testing
- Comprehensive documentation

This enhanced background sync service provides a robust, production-ready solution for keeping Google Sheets synchronized with your application data while maintaining optimal user experience and system reliability.
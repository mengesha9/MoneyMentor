#!/usr/bin/env python3
"""
Test Authentication Performance with Background Sync
Tests login performance when background sync service is running
"""
import asyncio
import time
import logging
import sys
import os
import statistics
from typing import List, Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthPerformanceTester:
    """Test authentication performance with background sync running"""
    
    def __init__(self):
        self.auth_times = []
        self.sync_running = False
        
    async def simulate_background_sync(self):
        """Simulate background sync operations that could interfere with auth"""
        from app.core.database import get_supabase
        
        logger.info("🔄 Starting background sync simulation")
        self.sync_running = True
        
        supabase = get_supabase()
        
        while self.sync_running:
            try:
                # Simulate various database operations that background sync would do
                
                # 1. Quiz responses query (heavy operation)
                await asyncio.to_thread(
                    lambda: supabase.table('quiz_responses').select('*').limit(100).execute()
                )
                
                # 2. User profiles query
                await asyncio.to_thread(
                    lambda: supabase.table('user_profiles').select('*').limit(50).execute()
                )
                
                # 3. Chat history query  
                await asyncio.to_thread(
                    lambda: supabase.table('chat_history').select('*').limit(50).execute()
                )
                
                # 4. Users query
                await asyncio.to_thread(
                    lambda: supabase.table('users').select('id, email, first_name, last_name').limit(50).execute()
                )
                
                # Small delay between operations to simulate real sync
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in background sync simulation: {e}")
                await asyncio.sleep(1)
        
        logger.info("🛑 Background sync simulation stopped")
    
    async def test_authentication_performance(self, test_duration: int = 30) -> Dict[str, Any]:
        """Test authentication performance over a period of time"""
        from app.core.auth import authenticate_user
        
        logger.info(f"🧪 Testing authentication performance for {test_duration} seconds")
        
        auth_times = []
        error_count = 0
        success_count = 0
        
        start_time = time.time()
        test_count = 0
        
        while (time.time() - start_time) < test_duration:
            test_count += 1
            
            try:
                # Time the authentication operation
                auth_start = time.time()
                
                # Use a test user for authentication
                result = await authenticate_user("test@example.com", "testpassword123")
                
                auth_end = time.time()
                auth_time = auth_end - auth_start
                
                if result:
                    auth_times.append(auth_time)
                    success_count += 1
                    
                    # Log slow authentications
                    if auth_time > 2.0:
                        logger.warning(f"⚠️  Slow authentication: {auth_time:.3f}s")
                    else:
                        logger.debug(f"✅ Authentication: {auth_time:.3f}s")
                else:
                    error_count += 1
                    logger.error(f"❌ Authentication failed")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Authentication error: {e}")
            
            # Wait a bit between tests
            await asyncio.sleep(0.5)
        
        # Calculate statistics
        if auth_times:
            avg_time = statistics.mean(auth_times)
            median_time = statistics.median(auth_times)
            min_time = min(auth_times)
            max_time = max(auth_times)
            std_dev = statistics.stdev(auth_times) if len(auth_times) > 1 else 0
            
            # Count slow authentications (> 2 seconds)
            slow_auths = len([t for t in auth_times if t > 2.0])
            very_slow_auths = len([t for t in auth_times if t > 5.0])
            
        else:
            avg_time = median_time = min_time = max_time = std_dev = 0
            slow_auths = very_slow_auths = 0
        
        results = {
            "test_duration": test_duration,
            "total_tests": test_count,
            "successful_auths": success_count,
            "failed_auths": error_count,
            "auth_times": auth_times,
            "average_time": avg_time,
            "median_time": median_time,
            "min_time": min_time,
            "max_time": max_time,
            "std_deviation": std_dev,
            "slow_auths_2s": slow_auths,
            "very_slow_auths_5s": very_slow_auths,
            "success_rate": (success_count / test_count * 100) if test_count > 0 else 0
        }
        
        return results
    
    async def run_performance_test(self):
        """Run the authentication performance test"""
        logger.info("🚀 Starting authentication performance test")
        
        try:
            # Test 1: Authentication without background sync
            logger.info("\n📊 TEST 1: Authentication without background sync")
            results_without_sync = await self.test_authentication_performance(15)
            
            # Test 2: Authentication with background sync
            logger.info("\n📊 TEST 2: Authentication with background sync")
            
            # Start background sync
            sync_task = asyncio.create_task(self.simulate_background_sync())
            
            # Wait a moment for sync to start
            await asyncio.sleep(2)
            
            # Run authentication tests
            results_with_sync = await self.test_authentication_performance(20)
            
            # Stop background sync
            self.sync_running = False
            await sync_task
            
            # Compare results
            self.compare_results(results_without_sync, results_with_sync)
            
        except Exception as e:
            logger.error(f"Error in performance test: {e}")
            raise
    
    def compare_results(self, without_sync: Dict[str, Any], with_sync: Dict[str, Any]):
        """Compare authentication performance results"""
        
        logger.info("\n" + "="*60)
        logger.info("📈 AUTHENTICATION PERFORMANCE COMPARISON")
        logger.info("="*60)
        
        logger.info(f"\n🔸 WITHOUT Background Sync:")
        logger.info(f"   • Total Tests: {without_sync['total_tests']}")
        logger.info(f"   • Success Rate: {without_sync['success_rate']:.1f}%")
        logger.info(f"   • Average Time: {without_sync['average_time']:.3f}s")
        logger.info(f"   • Median Time: {without_sync['median_time']:.3f}s")
        logger.info(f"   • Min/Max Time: {without_sync['min_time']:.3f}s / {without_sync['max_time']:.3f}s")
        logger.info(f"   • Std Deviation: {without_sync['std_deviation']:.3f}s")
        logger.info(f"   • Slow Auths (>2s): {without_sync['slow_auths_2s']}")
        logger.info(f"   • Very Slow Auths (>5s): {without_sync['very_slow_auths_5s']}")
        
        logger.info(f"\n🔸 WITH Background Sync:")
        logger.info(f"   • Total Tests: {with_sync['total_tests']}")
        logger.info(f"   • Success Rate: {with_sync['success_rate']:.1f}%")
        logger.info(f"   • Average Time: {with_sync['average_time']:.3f}s")
        logger.info(f"   • Median Time: {with_sync['median_time']:.3f}s")
        logger.info(f"   • Min/Max Time: {with_sync['min_time']:.3f}s / {with_sync['max_time']:.3f}s")
        logger.info(f"   • Std Deviation: {with_sync['std_deviation']:.3f}s")
        logger.info(f"   • Slow Auths (>2s): {with_sync['slow_auths_2s']}")
        logger.info(f"   • Very Slow Auths (>5s): {with_sync['very_slow_auths_5s']}")
        
        # Calculate performance impact
        if without_sync['average_time'] > 0:
            time_impact = ((with_sync['average_time'] - without_sync['average_time']) / without_sync['average_time']) * 100
        else:
            time_impact = 0
            
        success_rate_diff = with_sync['success_rate'] - without_sync['success_rate']
        
        logger.info(f"\n📊 PERFORMANCE IMPACT:")
        logger.info(f"   • Average Time Change: {time_impact:+.1f}%")
        logger.info(f"   • Success Rate Change: {success_rate_diff:+.1f}%")
        logger.info(f"   • Additional Slow Auths: {with_sync['slow_auths_2s'] - without_sync['slow_auths_2s']}")
        
        # Performance assessment
        logger.info(f"\n🎯 ASSESSMENT:")
        if time_impact < 20 and with_sync['slow_auths_2s'] < 3 and success_rate_diff > -5:
            logger.info("   ✅ EXCELLENT: Authentication performance is consistent with background sync")
        elif time_impact < 50 and with_sync['slow_auths_2s'] < 5 and success_rate_diff > -10:
            logger.info("   ✅ GOOD: Authentication performance is acceptable with background sync")
        elif time_impact < 100 and success_rate_diff > -20:
            logger.info("   ⚠️  FAIR: Some performance impact, but still acceptable")
        else:
            logger.info("   ❌ POOR: Significant performance degradation with background sync")
        
        logger.info("="*60)

async def main():
    """Main test function"""
    logger.info("🧪 Authentication Performance Test with Background Sync")
    logger.info("="*60)
    
    tester = AuthPerformanceTester()
    
    try:
        await tester.run_performance_test()
        logger.info("\n✅ Test completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Test interrupted by user")
        tester.sync_running = False
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        tester.sync_running = False
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

"""
Django middleware for database performance monitoring
Integrates enterprise monitoring with Django request lifecycle
"""

import time
import logging
from typing import Callable, Dict, Any

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from .monitoring import performance_monitor

logger = logging.getLogger('database.performance')


class DatabasePerformanceMiddleware(MiddlewareMixin):
    """
    Middleware to monitor database performance for all requests
    Tracks query performance, connection usage, and system metrics
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.monitor = performance_monitor
        
        # Configure monitoring based on settings
        self.enabled = getattr(settings, 'DB_PERFORMANCE_MONITORING', True)
        self.slow_query_threshold = getattr(settings, 'DB_SLOW_QUERY_THRESHOLD', 1.0)  # seconds
        
        if self.enabled:
            self.monitor.start_monitoring()
            logger.info("Database performance monitoring middleware enabled")
    
    def __call__(self, request):
        """Monitor the database performance during request processing"""
        if not self.enabled:
            return self.get_response(request)
        
        # Start monitoring
        start_time = time.time()
        request_path = request.get_full_path()
        request_method = request.method
        
        # Monitor queries for this request
        query_name = f"{request_method} {request_path}"
        
        with self.monitor.monitor_query(query_name):
            try:
                response = self.get_response(request)
                
                # Calculate request metrics
                request_time = time.time() - start_time
                
                # Log performance data
                self._log_request_metrics(
                    request_path=request_path,
                    request_method=request_method,
                    request_time=request_time,
                    response_status=response.status_code,
                    user=request.user.username if request.user.is_authenticated else 'anonymous'
                )
                
                # Add performance headers (useful for debugging)
                response['X-DB-Query-Time'] = f"{request_time:.3f}"
                response['X-DB-Monitoring'] = 'active'
                
                return response
                
            except Exception as e:
                # Log error with performance context
                logger.error(f"Request failed during monitoring: {query_name} - {str(e)}")
                raise
    
    def _log_request_metrics(self, 
                           request_path: str,
                           request_method: str,
                           request_time: float,
                           response_status: int,
                           user: str):
        """Log request performance metrics"""
        # Log slow requests
        if request_time > self.slow_query_threshold:
            logger.warning(
                f"SLOW REQUEST: {request_method} {request_path} - "
                f"{request_time:.3f}s - Status: {response_status} - User: {user}"
            )
        
        # Log detailed metrics for analysis
        logger.info(
            f"REQUEST_METRICS: {request_method} {request_path} - "
            f"Time: {request_time:.3f}s - Status: {response_status} - User: {user}"
        )
    
    def process_exception(self, request, exception):
        """Handle exceptions during request processing"""
        if self.enabled:
            logger.error(
                f"REQUEST_EXCEPTION: {request.method} {request.get_full_path()} - "
                f"Exception: {type(exception).__name__}: {str(exception)}"
            )
        
        # Continue with normal exception processing
        return None


class DatabaseHealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to periodically check database health
    Runs health checks in background and caches results
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.health_check_interval = getattr(settings, 'DB_HEALTH_CHECK_INTERVAL', 300)  # 5 minutes
        
        # Add health check endpoint
        self.health_endpoint = getattr(settings, 'DB_HEALTH_ENDPOINT', '/health/database')
    
    def __call__(self, request):
        """Handle health check requests"""
        if request.get_full_path() == self.health_endpoint:
            return self._health_check_response()
        
        return self.get_response(request)
    
    def _health_check_response(self) -> HttpResponse:
        """Generate health check response"""
        from .monitoring import health_checker
        
        try:
            health_data = health_checker.run_health_check()
            
            # Determine HTTP status based on overall health
            status_code = 200 if health_data['overall_status'] == 'healthy' else 503
            
            response = HttpResponse(
                content=str(health_data),
                content_type='application/json',
                status=status_code
            )
            
            # Add health status headers
            response['X-DB-Health'] = health_data['overall_status']
            response['X-Health-Timestamp'] = health_data['timestamp']
            
            return response
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HttpResponse(
                content='{"error": "Health check failed"}',
                content_type='application/json',
                status=503
            )


class DatabaseAnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware to collect analytics data for database performance
    Aggregates performance data for dashboard and reporting
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.analytics_enabled = getattr(settings, 'DB_ANALYTICS_ENABLED', True)
        
        if self.analytics_enabled:
            logger.info("Database analytics middleware enabled")
    
    def __call__(self, request):
        """Collect analytics during request processing"""
        if not self.analytics_enabled:
            return self.get_response(request)
        
        # Pre-request analytics collection
        pre_request_data = self._collect_pre_request_data(request)
        
        try:
            response = self.get_response(request)
            
            # Post-request analytics collection
            post_request_data = self._collect_post_request_data(response)
            
            # Combine and store analytics
            analytics_data = {
                **pre_request_data,
                **post_request_data,
                'timestamp': time.time()
            }
            
            self._store_analytics(analytics_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Analytics collection failed: {e}")
            raise
    
    def _collect_pre_request_data(self, request) -> Dict[str, Any]:
        """Collect data before request processing"""
        from django.db import connection
        
        return {
            'request_path': request.get_full_path(),
            'request_method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'user_authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'initial_query_count': len(connection.queries),
            'request_size': len(request.body) if hasattr(request, 'body') else 0
        }
    
    def _collect_post_request_data(self, response) -> Dict[str, Any]:
        """Collect data after request processing"""
        from django.db import connection
        
        return {
            'response_status': response.status_code,
            'response_size': len(response.content) if hasattr(response, 'content') else 0,
            'final_query_count': len(connection.queries),
            'content_type': response.get('Content-Type', ''),
            'cache_hit': hasattr(response, 'from_cache')
        }
    
    def _store_analytics(self, analytics_data: Dict[str, Any]):
        """Store analytics data for later processing"""
        try:
            # Calculate query performance
            query_count = analytics_data['final_query_count'] - analytics_data['initial_query_count']
            
            if query_count > 0:
                analytics_data['queries_per_request'] = query_count
                
                # Store in cache for aggregation
                from django.core.cache import cache
                
                # Get existing analytics
                cache_key = 'db_analytics_hourly'
                existing_analytics = cache.get(cache_key, [])
                
                # Add new analytics
                existing_analytics.append(analytics_data)
                
                # Keep only last 1000 entries
                if len(existing_analytics) > 1000:
                    existing_analytics = existing_analytics[-1000:]
                
                # Store back in cache
                cache.set(cache_key, existing_analytics, timeout=3600)  # 1 hour
                
                # Log significant events
                if query_count > 50:
                    logger.warning(
                        f"HIGH QUERY COUNT: {analytics_data['request_path']} - "
                        f"{query_count} queries"
                    )
                
                if analytics_data['response_status'] >= 500:
                    logger.error(
                        f"SERVER ERROR: {analytics_data['request_path']} - "
                        f"Status: {analytics_data['response_status']} - "
                        f"Queries: {query_count}"
                    )
                    
        except Exception as e:
            logger.error(f"Failed to store analytics: {e}")


class DatabaseMetricsMiddleware(MiddlewareMixin):
    """
    Middleware to expose database metrics via HTTP endpoints
    Provides real-time metrics for monitoring systems
    """
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.metrics_endpoint = getattr(settings, 'DB_METRICS_ENDPOINT', '/metrics/database')
        
        # Available metric endpoints
        self.metric_endpoints = {
            '/metrics/database': self._get_database_metrics,
            '/metrics/performance': self._get_performance_metrics,
            '/metrics/realtime': self._get_realtime_metrics,
            '/metrics/health': self._get_health_metrics
        }
    
    def __call__(self, request):
        """Handle metrics requests"""
        request_path = request.get_full_path()
        
        if request_path in self.metric_endpoints:
            return self.metric_endpoints[request_path](request)
        
        return self.get_response(request)
    
    def _get_database_metrics(self, request) -> HttpResponse:
        """Return comprehensive database metrics"""
        try:
            from .monitoring import performance_monitor
            
            # Get 24-hour summary
            metrics = performance_monitor.get_performance_summary(hours=24)
            
            return HttpResponse(
                content=str(metrics),
                content_type='application/json'
            )
            
        except Exception as e:
            return HttpResponse(
                content='{"error": str(e)}',
                content_type='application/json',
                status=500
            )
    
    def _get_performance_metrics(self, request) -> HttpResponse:
        """Return query performance metrics"""
        try:
            from .monitoring import performance_monitor
            
            # Get last 100 queries
            real_time = performance_monitor.get_real_time_metrics()
            
            return HttpResponse(
                content=str(real_time),
                content_type='application/json'
            )
            
        except Exception as e:
            return HttpResponse(
                content='{"error": str(e)}',
                content_type='application/json',
                status=500
            )
    
    def _get_realtime_metrics(self, request) -> HttpResponse:
        """Return real-time system metrics"""
        try:
            from .monitoring import performance_monitor
            
            # Get current metrics
            real_time = performance_monitor.get_real_time_metrics()
            
            return HttpResponse(
                content=str(real_time),
                content_type='application/json'
            )
            
        except Exception as e:
            return HttpResponse(
                content='{"error": str(e)}',
                content_type='application/json',
                status=500
            )
    
    def _get_health_metrics(self, request) -> HttpResponse:
        """Return health check metrics"""
        try:
            from .monitoring import health_checker
            
            # Run health check
            health = health_checker.run_health_check()
            
            return HttpResponse(
                content=str(health),
                content_type='application/json'
            )
            
        except Exception as e:
            return HttpResponse(
                content='{"error": str(e)}',
                content_type='application/json',
                status=500
            )
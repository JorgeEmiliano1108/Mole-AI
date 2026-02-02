"""
Enterprise-grade database performance monitoring system
Real-time monitoring, alerting, and analytics for Mole AI database
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import contextmanager
import logging
import json

from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min

logger = logging.getLogger('database.performance')


@dataclass
class QueryMetrics:
    """Metrics for individual query performance"""
    query: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    user: Optional[str] = None
    app_name: Optional[str] = None
    slow_query: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query[:200] + '...' if len(self.query) > 200 else self.query,
            'execution_time_ms': self.execution_time * 1000,
            'rows_affected': self.rows_affected,
            'timestamp': self.timestamp.isoformat(),
            'user': self.user,
            'app_name': self.app_name,
            'slow_query': self.slow_query
        }


@dataclass 
class DatabaseMetrics:
    """Overall database performance metrics"""
    timestamp: datetime
    active_connections: int
    idle_connections: int
    total_connections: int
    cache_hit_ratio: float
    slow_queries_count: int
    avg_query_time: float
    max_query_time: float
    disk_usage_mb: float
    memory_usage_mb: float
    cpu_usage_percent: float


class DatabasePerformanceMonitor:
    """
    Enterprise-grade performance monitoring for PostgreSQL
    Monitors queries, connections, and system resources
    """
    
    def __init__(self, 
                 slow_query_threshold: float = 1.0,  # seconds
                 monitoring_interval: int = 60,  # seconds
                 metrics_retention_hours: int = 24):
        self.slow_query_threshold = slow_query_threshold
        self.monitoring_interval = monitoring_interval
        self.metrics_retention_hours = metrics_retention_hours
        
        self.query_metrics: List[QueryMetrics] = []
        self.db_metrics: List[DatabaseMetrics] = []
        self.monitoring_active = False
        self._monitor_thread = None
        self._lock = threading.Lock()
        
        # Performance thresholds for alerting
        self.thresholds = {
            'max_connections': 80,
            'max_cpu_percent': 80.0,
            'max_memory_mb': 2048,
            'max_disk_usage_mb': 10240,
            'min_cache_hit_ratio': 0.85,
            'max_slow_queries_per_min': 5
        }
    
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, 
                daemon=True
            )
            self._monitor_thread.start()
            logger.info("Database performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Database performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect database metrics
                db_metrics = self._collect_database_metrics()
                
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                
                # Combine metrics
                combined_metrics = DatabaseMetrics(
                    timestamp=timezone.now(),
                    **db_metrics,
                    **system_metrics
                )
                
                # Store metrics
                with self._lock:
                    self.db_metrics.append(combined_metrics)
                    self._cleanup_old_metrics()
                
                # Check for alerts
                self._check_alerts(combined_metrics)
                
                # Store in cache for external monitoring systems
                cache.set(
                    'db_performance_metrics',
                    combined_metrics.to_dict() if hasattr(combined_metrics, 'to_dict') else vars(combined_metrics),
                    timeout=300  # 5 minutes
                )
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect PostgreSQL-specific metrics"""
        try:
            with connection.cursor() as cursor:
                # Get connection statistics
                cursor.execute("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                conn_stats = cursor.fetchone()
                
                # Get cache hit ratio
                cursor.execute("""
                    SELECT 
                        heap_blks_hit,
                        heap_blks_read,
                        (heap_blks_hit::float / NULLIF(heap_blks_hit + heap_blks_read, 0)) as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                cache_stats = cursor.fetchone()
                
                # Get slow queries count (last minute)
                cursor.execute("""
                    SELECT count(*) as slow_queries
                    FROM pg_stat_statements 
                    WHERE mean_exec_time > %s
                    AND calls > 0
                    AND datname = current_database()
                """, [self.slow_query_threshold * 1000])  # Convert to milliseconds
                slow_stats = cursor.fetchone()
                
                return {
                    'active_connections': conn_stats['active_connections'],
                    'idle_connections': conn_stats['idle_connections'],
                    'total_connections': conn_stats['total_connections'],
                    'cache_hit_ratio': cache_stats['cache_hit_ratio'] or 0.0,
                    'slow_queries_count': slow_stats['slow_queries']
                }
                
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {
                'active_connections': 0,
                'idle_connections': 0,
                'total_connections': 0,
                'cache_hit_ratio': 0.0,
                'slow_queries_count': 0
            }
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_mb = memory.used / 1024 / 1024
            
            # Disk usage (assuming database on same disk)
            disk = psutil.disk_usage('/')
            disk_usage_mb = disk.used / 1024 / 1024
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_mb': memory_usage_mb,
                'disk_usage_mb': disk_usage_mb
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {
                'cpu_usage_percent': 0.0,
                'memory_usage_mb': 0.0,
                'disk_usage_mb': 0.0
            }
    
    def _check_alerts(self, metrics: DatabaseMetrics):
        """Check metrics against thresholds and trigger alerts"""
        alerts = []
        
        # Connection alerts
        if metrics.total_connections > self.thresholds['max_connections']:
            alerts.append({
                'type': 'connection_alert',
                'severity': 'warning',
                'message': f"High connection count: {metrics.total_connections}",
                'timestamp': timezone.now().isoformat()
            })
        
        # CPU alerts
        if metrics.cpu_usage_percent > self.thresholds['max_cpu_percent']:
            alerts.append({
                'type': 'cpu_alert',
                'severity': 'critical',
                'message': f"High CPU usage: {metrics.cpu_usage_percent}%",
                'timestamp': timezone.now().isoformat()
            })
        
        # Memory alerts
        if metrics.memory_usage_mb > self.thresholds['max_memory_mb']:
            alerts.append({
                'type': 'memory_alert',
                'severity': 'warning',
                'message': f"High memory usage: {metrics.memory_usage_mb}MB",
                'timestamp': timezone.now().isoformat()
            })
        
        # Cache hit ratio alerts
        if metrics.cache_hit_ratio < self.thresholds['min_cache_hit_ratio']:
            alerts.append({
                'type': 'cache_alert',
                'severity': 'warning',
                'message': f"Low cache hit ratio: {metrics.cache_hit_ratio:.2%}",
                'timestamp': timezone.now().isoformat()
            })
        
        # Slow queries alerts
        if metrics.slow_queries_count > self.thresholds['max_slow_queries_per_min']:
            alerts.append({
                'type': 'slow_query_alert',
                'severity': 'critical',
                'message': f"High slow query count: {metrics.slow_queries_count}/min",
                'timestamp': timezone.now().isoformat()
            })
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"DATABASE ALERT: {alert}")
            
        # Store alerts in cache for dashboard
        if alerts:
            cache.set(
                'db_performance_alerts',
                alerts,
                timeout=3600  # 1 hour
            )
    
    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period"""
        cutoff_time = timezone.now() - timedelta(hours=self.metrics_retention_hours)
        
        # Clean old database metrics
        self.db_metrics = [
            m for m in self.db_metrics 
            if m.timestamp > cutoff_time
        ]
        
        # Clean old query metrics
        self.query_metrics = [
            q for q in self.query_metrics 
            if q.timestamp > cutoff_time
        ]
    
    @contextmanager
    def monitor_query(self, query_name: str = "unknown"):
        """Context manager to monitor individual query performance"""
        start_time = time.time()
        
        # Reset query count for this monitoring session
        initial_queries = len(connection.queries)
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            # Count queries executed in this context
            query_count = len(connection.queries) - initial_queries
            
            # Create metrics for each query
            for i in range(query_count):
                if initial_queries + i < len(connection.queries):
                    query_info = connection.queries[initial_queries + i]
                    query_metric = QueryMetrics(
                        query=query_info.get('sql', ''),
                        execution_time=execution_time / query_count if query_count > 0 else execution_time,
                        rows_affected=0,  # Would need additional tracking
                        timestamp=timezone.now(),
                        query_name=query_name,
                        slow_query=execution_time > self.slow_query_threshold
                    )
                    
                    with self._lock:
                        self.query_metrics.append(query_metric)
                        
                    # Log slow queries
                    if query_metric.slow_query:
                        logger.warning(
                            f"SLOW QUERY DETECTED: {query_metric.execution_time:.3f}s - "
                            f"{query_metric.query[:200]}..."
                        )
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_db_metrics = [
            m for m in self.db_metrics 
            if m.timestamp > cutoff_time
        ]
        
        recent_queries = [
            q for q in self.query_metrics 
            if q.timestamp > cutoff_time
        ]
        
        if not recent_db_metrics:
            return {
                'error': 'No metrics available for specified time period',
                'period_hours': hours
            }
        
        # Calculate aggregates
        avg_cpu = sum(m.cpu_usage_percent for m in recent_db_metrics) / len(recent_db_metrics)
        max_cpu = max(m.cpu_usage_percent for m in recent_db_metrics)
        avg_memory = sum(m.memory_usage_mb for m in recent_db_metrics) / len(recent_db_metrics)
        max_memory = max(m.memory_usage_mb for m in recent_db_metrics)
        avg_connections = sum(m.total_connections for m in recent_db_metrics) / len(recent_db_metrics)
        max_connections = max(m.total_connections for m in recent_db_metrics)
        avg_cache_hit = sum(m.cache_hit_ratio for m in recent_db_metrics) / len(recent_db_metrics)
        
        # Query metrics
        slow_queries = [q for q in recent_queries if q.slow_query]
        avg_query_time = sum(q.execution_time for q in recent_queries) / len(recent_queries) if recent_queries else 0
        max_query_time = max(q.execution_time for q in recent_queries) if recent_queries else 0
        
        return {
            'period_hours': hours,
            'database_metrics': {
                'avg_connections': round(avg_connections, 2),
                'max_connections': max_connections,
                'avg_cache_hit_ratio': round(avg_cache_hit, 4),
                'total_slow_queries': len(slow_queries),
                'slow_query_percentage': round(len(slow_queries) / len(recent_queries) * 100, 2) if recent_queries else 0
            },
            'query_performance': {
                'total_queries': len(recent_queries),
                'avg_query_time_ms': round(avg_query_time * 1000, 2),
                'max_query_time_ms': round(max_query_time * 1000, 2),
                'slow_queries': [
                    q.to_dict() for q in slow_queries[-10:]  # Last 10 slow queries
                ]
            },
            'system_performance': {
                'avg_cpu_percent': round(avg_cpu, 2),
                'max_cpu_percent': round(max_cpu, 2),
                'avg_memory_mb': round(avg_memory, 2),
                'max_memory_mb': round(max_memory, 2)
            },
            'timestamp': timezone.now().isoformat()
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get most recent performance metrics"""
        if not self.db_metrics:
            return {'error': 'No metrics available'}
        
        latest_metrics = self.db_metrics[-1]
        
        # Get recent slow queries
        recent_slow = [
            q.to_dict() for q in self.query_metrics[-20:] 
            if q.slow_query
        ]
        
        return {
            'current_metrics': vars(latest_metrics),
            'recent_slow_queries': recent_slow,
            'monitoring_status': 'active' if self.monitoring_active else 'inactive',
            'timestamp': timezone.now().isoformat()
        }


class DatabaseHealthChecker:
    """
    Automated database health checks and diagnostics
    """
    
    def __init__(self):
        self.health_checks = [
            self._check_connection_health,
            self._check_query_performance,
            self._check_index_usage,
            self._check_table_bloat,
            self._check_vacuum_status,
            self._check_backup_status
        ]
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        results = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'recommendations': []
        }
        
        for check_func in self.health_checks:
            try:
                check_result = check_func()
                results['checks'][check_func.__name__] = check_result
                
                if check_result['status'] != 'healthy':
                    results['overall_status'] = 'degraded'
                    results['recommendations'].extend(check_result.get('recommendations', []))
                    
            except Exception as e:
                results['checks'][check_func.__name__] = {
                    'status': 'error',
                    'message': str(e)
                }
                results['overall_status'] = 'error'
                results['recommendations'].append(f"Fix error in {check_func.__name__}: {e}")
        
        return results
    
    def _check_connection_health(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return {
                    'status': 'healthy',
                    'message': 'Database connection successful'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {e}',
                'recommendations': ['Check database server status', 'Verify connection settings']
            }
    
    def _check_query_performance(self) -> Dict[str, Any]:
        """Check query performance metrics"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        mean_exec_time,
                        max_exec_time,
                        calls,
                        total_exec_time
                    FROM pg_stat_statements 
                    WHERE datname = current_database()
                    ORDER BY mean_exec_time DESC
                    LIMIT 5
                """)
                slow_queries = cursor.fetchall()
                
                if slow_queries and slow_queries[0]['mean_exec_time'] > 1000:  # 1 second
                    return {
                        'status': 'degraded',
                        'message': 'Slow queries detected',
                        'data': slow_queries,
                        'recommendations': [
                            'Optimize slow queries',
                            'Add missing indexes',
                            'Analyze query execution plans'
                        ]
                    }
                
                return {
                    'status': 'healthy',
                    'message': 'Query performance acceptable',
                    'data': slow_queries
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Query performance check failed: {e}'
            }
    
    def _check_index_usage(self) -> Dict[str, Any]:
        """Check index usage and efficiency"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """)
                index_stats = cursor.fetchall()
                
                # Check for unused indexes
                unused_indexes = [idx for idx in index_stats if idx['idx_scan'] == 0]
                
                if unused_indexes:
                    return {
                        'status': 'degraded',
                        'message': f'{len(unused_indexes)} unused indexes found',
                        'data': unused_indexes,
                        'recommendations': ['Remove unused indexes', 'Review index strategy']
                    }
                
                return {
                    'status': 'healthy',
                    'message': 'Index usage acceptable',
                    'data': index_stats
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Index usage check failed: {e}'
            }
    
    def _check_table_bloat(self) -> Dict[str, Any]:
        """Check for table bloat"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        ROUND(CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages/otta::numeric END,1) AS bloat_ratio,
                        CASE WHEN otta=0 THEN 0 ELSE sml.relpages-otta::numeric END AS extra_pages,
                        (sml.relpages*8192)::bigint AS bloat_bytes
                    FROM (
                        SELECT 
                            ma.schemaname,
                            ma.tablename,
                            bs.relpages AS sml_relpages,
                            CEIL((ma.tups*((bs.hdr+ma.ma)+(bs.hdr+fillfactor*ma.tups::bigint))/(bs.page_size::float))::numeric) AS otta
                        FROM (
                            SELECT 
                                schemaname, tablename, tups, fillfactor, ma
                            FROM pg_stats
                        ) AS ma
                        JOIN (
                            SELECT 
                                hdr, page_size
                            FROM pg_settings 
                            WHERE name IN ('block_header_size', 'page_size')
                        ) AS bs ON ma.pagesize=bs.page_size
                    ) AS mb
                    WHERE ma.schemaname='public'
                """)
                bloat_stats = cursor.fetchall()
                
                high_bloat = [tbl for tbl in bloat_stats if tbl['bloat_ratio'] > 0.2]
                
                if high_bloat:
                    return {
                        'status': 'degraded',
                        'message': f'{len(high_bloat)} tables with high bloat',
                        'data': high_bloat,
                        'recommendations': ['Run VACUUM on bloated tables', 'Consider autovacuum tuning']
                    }
                
                return {
                    'status': 'healthy',
                    'message': 'Table bloat acceptable',
                    'data': bloat_stats
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Table bloat check failed: {e}'
            }
    
    def _check_vacuum_status(self) -> Dict[str, Any]:
        """Check vacuum and autovacuum status"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                """)
                vacuum_stats = cursor.fetchall()
                
                # Check for tables needing vacuum
                old_vacuum = [
                    tbl for tbl in vacuum_stats 
                    if tbl['last_vacuum'] and tbl['last_vacuum'] < (timezone.now() - timedelta(days=7))
                ]
                
                if old_vacuum:
                    return {
                        'status': 'degraded',
                        'message': f'{len(old_vacuum)} tables need vacuum',
                        'data': old_vacuum,
                        'recommendations': ['Schedule regular VACUUM', 'Check autovacuum settings']
                    }
                
                return {
                    'status': 'healthy',
                    'message': 'Vacuum status acceptable',
                    'data': vacuum_stats
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Vacuum status check failed: {e}'
            }
    
    def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup status (placeholder implementation)"""
        # This would integrate with your backup system
        return {
            'status': 'info',
            'message': 'Backup status check not implemented',
            'recommendations': ['Implement backup status monitoring']
        }


# Global monitor instance
performance_monitor = DatabasePerformanceMonitor()
health_checker = DatabaseHealthChecker()
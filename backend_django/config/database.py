"""
Enterprise-grade database connection management for Mole AI
Implements advanced connection pooling, health checks, and monitoring
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager
import threading
from queue import Queue, Empty

import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('database.connection')


class ConnectionPoolManager:
    """
    Enterprise-grade connection pool manager with health monitoring
    """
    
    def __init__(self, 
                 min_connections: int = 5,
                 max_connections: int = 100,
                 connection_timeout: float = 30.0,
                 idle_timeout: float = 600.0,
                 max_lifetime: float = 3600.0):
        """
        Initialize connection pool with enterprise settings
        
        Args:
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
            connection_timeout: Timeout for acquiring connections
            idle_timeout: Close connections idle longer than this
            max_lifetime: Maximum lifetime for connections
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        self.max_lifetime = max_lifetime
        
        self.pool: Optional[pool.ThreadedConnectionPool] = None
        self._lock = threading.Lock()
        self._stats = {
            'total_connections': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0,
            'last_health_check': 0
        }
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the PostgreSQL connection pool"""
        try:
            database_url = self._get_database_url()
            
            self.pool = pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                dsn=database_url,
                cursor_factory=DictCursor,
                connection_timeout=self.connection_timeout
            )
            
            self._stats['total_connections'] = self.min_connections
            logger.info(f"Connection pool initialized: {self.min_connections}-{self.max_connections} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise ImproperlyConfigured(f"Database connection pool initialization failed: {e}")
    
    def _get_database_url(self) -> str:
        """Construct database URL from Django settings"""
        try:
            db_config = settings.DATABASES['default']
            return (
                f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}"
                f"@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
                f"?sslmode={db_config.get('OPTIONS', {}).get('sslmode', 'prefer')}"
            )
        except KeyError as e:
            raise ImproperlyConfigured(f"Missing database configuration: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting database connection from pool
        
        Yields:
            psycopg2 connection object
        """
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        connection = None
        try:
            # Try to get connection from pool
            connection = self.pool.getconn(timeout=self.connection_timeout)
            self._stats['active_connections'] += 1
            self._stats['pool_hits'] += 1
            
            # Verify connection is alive
            if not self._is_connection_healthy(connection):
                self._stats['connection_errors'] += 1
                self.pool.putconn(connection, close=True)
                connection = self.pool.getconn(timeout=self.connection_timeout)
            
            yield connection
            
        except pool.PoolError as e:
            self._stats['pool_misses'] += 1
            logger.warning(f"Connection pool exhausted: {e}")
            raise
            
        except Exception as e:
            self._stats['connection_errors'] += 1
            logger.error(f"Database connection error: {e}")
            raise
            
        finally:
            if connection:
                try:
                    self.pool.putconn(connection)
                    self._stats['active_connections'] -= 1
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
    
    def _is_connection_healthy(self, connection) -> bool:
        """Check if connection is healthy and responsive"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self.pool:
            stats = self._stats.copy()
            stats.update({
                'pool_size': self.pool.minconn,
                'max_connections': self.pool.maxconn,
                'available_connections': self.pool._queue.qsize(),
                'pool_utilization': self._stats['active_connections'] / self.pool.maxconn * 100
            })
            return stats
        return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of connection pool"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Test basic connectivity
                    cursor.execute("SELECT 1")
                    
                    # Get database metrics
                    cursor.execute("""
                        SELECT 
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections,
                            count(*) FILTER (WHERE state = 'idle') as idle_connections
                        FROM pg_stat_activity 
                        WHERE datname = current_database()
                    """)
                    db_stats = cursor.fetchone()
                    
                    # Test query performance
                    start_time = time.time()
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables")
                    cursor.fetchone()
                    query_time = time.time() - start_time
                    
                    self._stats['last_health_check'] = time.time()
                    
                    return {
                        'pool_healthy': True,
                        'database_accessible': True,
                        'query_performance_ms': query_time * 1000,
                        'database_connections': dict(db_stats),
                        'pool_stats': self.get_pool_stats(),
                        'last_check': self._stats['last_health_check']
                    }
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'pool_healthy': False,
                'database_accessible': False,
                'error': str(e),
                'last_check': time.time()
            }
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            self._stats['total_connections'] = 0
            self._stats['active_connections'] = 0
            logger.info("All database connections closed")


class DatabaseRouter:
    """
    Enterprise database router for read/write splitting and service isolation
    """
    
    def __init__(self):
        self.read_pool = ConnectionPoolManager(
            min_connections=10,
            max_connections=50,
            connection_timeout=30.0
        )
        self.write_pool = ConnectionPoolManager(
            min_connections=5,
            max_connections=20,
            connection_timeout=30.0
        )
        self.service_pools = {
            'vision': ConnectionPoolManager(min_connections=3, max_connections=15),
            'rag': ConnectionPoolManager(min_connections=3, max_connections=15),
            'core': ConnectionPoolManager(min_connections=5, max_connections=30)
        }
    
    def get_pool(self, service: str = 'core', read_only: bool = False):
        """Get appropriate connection pool for service and operation type"""
        if read_only and service == 'core':
            return self.read_pool
        elif service in self.service_pools:
            return self.service_pools[service]
        else:
            return self.write_pool
    
    def health_check_all(self) -> Dict[str, Any]:
        """Health check for all connection pools"""
        results = {
            'read_pool': self.read_pool.health_check(),
            'write_pool': self.write_pool.health_check(),
            'service_pools': {
                name: pool.health_check() 
                for name, pool in self.service_pools.items()
            },
            'timestamp': time.time()
        }
        return results


# Global database router instance
db_router = DatabaseRouter()


# Django database backend configuration
def configure_django_database():
    """
    Configure Django settings for enterprise database connection
    Call this from Django settings.py
    """
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'mole_ai_db'),
            'USER': os.getenv('POSTGRES_USER', 'mole_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.getenv('DB_SSL_MODE', 'prefer'),
                'connect_timeout': 30,
                'application_name': 'mole_ai_backend',
                'tcp_keepalives_idle': 600,
                'tcp_keepalives_interval': 30,
                'tcp_keepalives_count': 3,
            },
            'CONN_MAX_AGE': 600,  # 10 minutes
            'ATOMIC_REQUESTS': True,
        }
    }
    
    # Read replica configuration (if available)
    if os.getenv('POSTGRES_READ_REPLICA_HOST'):
        DATABASES['replica'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'mole_ai_db'),
            'USER': os.getenv('POSTGRES_USER', 'mole_user'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_READ_REPLICA_HOST'),
            'PORT': os.getenv('POSTGRES_READ_REPLICA_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.getenv('DB_SSL_MODE', 'prefer'),
                'connect_timeout': 30,
                'application_name': 'mole_ai_read_replica',
            },
            'CONN_MAX_AGE': 600,
        }
    
    return DATABASES


class DatabaseHealthMonitor:
    """
    Continuous database health monitoring and alerting
    """
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self):
        """Start continuous health monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            logger.info("Database health monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Database health monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                health = db_router.health_check_all()
                self._analyze_health(health)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def _analyze_health(self, health_data: Dict[str, Any]):
        """Analyze health data and trigger alerts if needed"""
        for pool_name, pool_health in health_data['service_pools'].items():
            if not pool_health.get('pool_healthy', False):
                logger.error(f"ALERT: {pool_name} connection pool unhealthy!")
            
            if pool_health.get('query_performance_ms', 0) > 1000:
                logger.warning(f"WARNING: {pool_name} slow queries detected "
                            f"({pool_health['query_performance_ms']:.2f}ms)")
        
        # Check overall database health
        if not health_data['read_pool']['pool_healthy']:
            logger.critical("CRITICAL: Read database pool failed!")
        
        if not health_data['write_pool']['pool_healthy']:
            logger.critical("CRITICAL: Write database pool failed!")


# Global health monitor instance
health_monitor = DatabaseHealthMonitor(check_interval=60)
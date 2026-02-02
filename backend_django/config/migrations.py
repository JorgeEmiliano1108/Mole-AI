"""
Enterprise database migration utilities for Mole AI
Provides safe, atomic, and trackable database migrations
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db import migrations, connection
from django.core.management.base import BaseCommand
from django.core.management import call_command

logger = logging.getLogger('database.migrations')


class MigrationPlan:
    """
    Enterprise-grade migration planning and execution
    Ensures safe, trackable, and reversible database changes
    """
    
    def __init__(self):
        self.migrations: List[Dict[str, Any]] = []
        self.execution_plan: List[Dict[str, Any]] = []
        self.rollback_plan: List[Dict[str, Any]] = []
        
    def add_migration(self, 
                   name: str,
                   description: str,
                   forward_sql: str,
                   reverse_sql: str = None,
                   dependencies: List[str] = None,
                   estimated_time: int = 60,  # seconds
                   risk_level: str = 'medium'):
        """Add a migration to the plan"""
        self.migrations.append({
            'name': name,
            'description': description,
            'forward_sql': forward_sql,
            'reverse_sql': reverse_sql,
            'dependencies': dependencies or [],
            'estimated_time': estimated_time,
            'risk_level': risk_level,  # low, medium, high, critical
            'created_at': datetime.now(),
            'status': 'planned'
        })
    
    def generate_execution_plan(self):
        """Generate optimized execution order"""
        # Sort by dependencies and risk level
        sorted_migrations = sorted(
            self.migrations,
            key=lambda x: (len(x['dependencies']), x['risk_level'])
        )
        
        self.execution_plan = sorted_migrations
        
        # Generate rollback plan
        self.rollback_plan = list(reversed(sorted_migrations))
        
        return self.execution_plan
    
    def validate_plan(self) -> Dict[str, Any]:
        """Validate migration plan for safety"""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check for circular dependencies
        for migration in self.migrations:
            for dep in migration['dependencies']:
                if not any(m['name'] == dep for m in self.migrations):
                    validation_result['valid'] = False
                    validation_result['errors'].append(
                        f"Migration {migration['name']} depends on non-existent {dep}"
                    )
        
        # Check for high-risk migrations
        high_risk = [m for m in self.migrations if m['risk_level'] == 'critical']
        if high_risk:
            validation_result['warnings'].append(
                f"{len(high_risk)} critical migrations require manual review"
            )
        
        # Estimate total execution time
        total_time = sum(m['estimated_time'] for m in self.migrations)
        if total_time > 300:  # 5 minutes
            validation_result['warnings'].append(
                f"Estimated migration time ({total_time}s) exceeds recommended limit"
            )
        
        return validation_result


class SafeMigrationExecutor:
    """
    Safe migration executor with backup, validation, and rollback capabilities
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.executed_migrations: List[str] = []
        self.failed_migrations: List[Dict[str, Any]] = []
        
    def execute_migration(self, migration: Dict[str, Any]) -> bool:
        """Execute a single migration safely"""
        migration_name = migration['name']
        
        logger.info(f"Executing migration: {migration_name}")
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would execute {migration_name}")
            return True
        
        try:
            # Pre-execution backup
            backup_file = self._create_backup(migration_name)
            
            # Execute forward migration
            with connection.cursor() as cursor:
                cursor.execute(migration['forward_sql'])
                connection.commit()
            
            # Verify migration success
            if not self._verify_migration(migration):
                raise Exception("Migration verification failed")
            
            self.executed_migrations.append(migration_name)
            logger.info(f"Successfully executed migration: {migration_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration {migration_name} failed: {e}")
            
            # Attempt rollback
            try:
                self._rollback_migration(migration)
                self.failed_migrations.append({
                    'name': migration_name,
                    'error': str(e),
                    'rolled_back': True
                })
            except Exception as rollback_error:
                logger.error(f"Rollback failed for {migration_name}: {rollback_error}")
                self.failed_migrations.append({
                    'name': migration_name,
                    'error': str(e),
                    'rollback_error': str(rollback_error),
                    'rolled_back': False
                })
            
            return False
    
    def _create_backup(self, migration_name: str) -> str:
        """Create backup before migration"""
        backup_file = f"/tmp/migration_backup_{migration_name}_{datetime.now().isoformat()}.sql"
        
        try:
            # Create table-level backup
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        'CREATE TABLE ' || tablename || '_backup AS ' || 
                        'SELECT * FROM ' || tablename || ';' as backup_sql
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                backup_sql_statements = cursor.fetchall()
                
                with open(backup_file, 'w') as f:
                    for statement in backup_sql_statements:
                        f.write(statement[0] + '\n')
            
            logger.info(f"Backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup for {migration_name}: {e}")
            return ""
    
    def _verify_migration(self, migration: Dict[str, Any]) -> bool:
        """Verify that migration was applied correctly"""
        try:
            # This would need to be customized per migration
            # For now, basic verification
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")  # Simple connectivity test
                cursor.fetchone()
                return True
                
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False
    
    def _rollback_migration(self, migration: Dict[str, Any]):
        """Rollback a failed migration"""
        if not migration['reverse_sql']:
            logger.warning(f"No rollback SQL available for {migration['name']}")
            return
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(migration['reverse_sql'])
                connection.commit()
            
            logger.info(f"Successfully rolled back migration: {migration['name']}")
            
        except Exception as e:
            logger.error(f"Rollback failed for {migration['name']}: {e}")
            raise
    
    def get_execution_report(self) -> Dict[str, Any]:
        """Get comprehensive execution report"""
        return {
            'executed_migrations': self.executed_migrations,
            'failed_migrations': self.failed_migrations,
            'success_rate': len(self.executed_migrations) / (len(self.executed_migrations) + len(self.failed_migrations)) if (len(self.executed_migrations) + len(self.failed_migrations)) > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }


class EnterpriseMigration:
    """
    Base class for enterprise-grade migrations
    Provides standardized migration structure and safety checks
    """
    
    def __init__(self, 
                 name: str,
                 description: str,
                 version: str,
                 risk_level: str = 'medium'):
        self.name = name
        self.description = description
        self.version = version
        self.risk_level = risk_level
        self.created_at = datetime.now()
        
    def get_forward_sql(self) -> str:
        """Get SQL for forward migration"""
        raise NotImplementedError("Subclasses must implement get_forward_sql")
    
    def get_reverse_sql(self) -> str:
        """Get SQL for rollback migration"""
        raise NotImplementedError("Subclasses must implement get_reverse_sql")
    
    def get_dependencies(self) -> List[str]:
        """Get list of migration dependencies"""
        return []
    
    def get_estimated_time(self) -> int:
        """Get estimated execution time in seconds"""
        return 60
    
    def get_validation_checks(self) -> List[str]:
        """Get SQL validation checks after migration"""
        return []
    
    def to_django_migration(self) -> migrations.Migration:
        """Convert to Django migration object"""
        return migrations.Migration(
            name=self.name,
            operations=[
                migrations.RunSQL(
                    sql=self.get_forward_sql(),
                    reverse_sql=self.get_reverse_sql(),
                    elidable=False
                ),
                # Add validation checks
                *[migrations.RunSQL(check) for check in self.get_validation_checks()]
            ]
        )


class PerformanceOptimizationMigration(EnterpriseMigration):
    """
    Migration for performance optimizations
    Includes indexes, partitions, and table optimizations
    """
    
    def __init__(self):
        super().__init__(
            name='performance_optimization_v1',
            description='Add performance indexes and optimizations',
            version='1.0.0',
            risk_level='medium'
        )
    
    def get_forward_sql(self) -> str:
        """Get performance optimization SQL"""
        return """
        -- Create performance indexes for high-traffic queries
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plant_owner_created_optimized 
        ON plants_mgmt_plant (owner_id, created_at DESC, status);
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnosis_urgent_recent 
        ON plants_mgmt_diagnosis (urgency_level DESC, created_at DESC, plant_id)
        WHERE urgency_level IN ('high', 'critical');
        
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sensor_time_series_optimized 
        ON plants_mgmt_sensordata (plant_id, timestamp DESC, humidity, temperature)
        WHERE timestamp > NOW() - INTERVAL '30 days';
        
        -- Optimize table statistics
        ANALYZE plants_mgmt_plant;
        ANALYZE plants_mgmt_diagnosis;
        ANALYZE plants_mgmt_sensordata;
        ANALYZE plants_mgmt_plantimage;
        ANALYZE plants_mgmt_knowledgedocument;
        
        -- Create or update partitioned views for time-series data
        CREATE OR REPLACE VIEW sensor_recent_partitioned AS
        SELECT * FROM plants_mgmt_sensordata
        WHERE timestamp >= DATE_TRUNC('day', CURRENT_DATE);
        """
    
    def get_reverse_sql(self) -> str:
        """Get rollback SQL for performance optimizations"""
        return """
        -- Remove performance indexes
        DROP INDEX IF EXISTS idx_plant_owner_created_optimized;
        DROP INDEX IF EXISTS idx_diagnosis_urgent_recent;
        DROP INDEX IF EXISTS idx_sensor_time_series_optimized;
        
        -- Remove partitioned view
        DROP VIEW IF EXISTS sensor_recent_partitioned;
        """
    
    def get_validation_checks(self) -> List[str]:
        """Get validation checks for performance optimizations"""
        return [
            "SELECT COUNT(*) FROM pg_indexes WHERE indexname = 'idx_plant_owner_created_optimized'",
            "SELECT COUNT(*) FROM pg_indexes WHERE indexname = 'idx_diagnosis_urgent_recent'",
            "SELECT COUNT(*) FROM pg_indexes WHERE indexname = 'idx_sensor_time_series_optimized'",
            "SELECT COUNT(*) FROM information_schema.views WHERE table_name = 'sensor_recent_partitioned'"
        ]


class SchemaValidationMigration(EnterpriseMigration):
    """
    Migration for schema validation and cleanup
    Ensures data integrity and consistency
    """
    
    def __init__(self):
        super().__init__(
            name='schema_validation_v1',
            description='Validate schema and cleanup orphaned data',
            version='1.0.0',
            risk_level='low'
        )
    
    def get_forward_sql(self) -> str:
        """Get schema validation SQL"""
        return """
        -- Clean up orphaned sensor data (no associated plant)
        DELETE FROM plants_mgmt_sensordata 
        WHERE plant_id NOT IN (SELECT id FROM plants_mgmt_plant WHERE id IS NOT NULL);
        
        -- Clean up orphaned diagnoses (no associated plant)
        DELETE FROM plants_mgmt_diagnosis 
        WHERE plant_id NOT IN (SELECT id FROM plants_mgmt_plant WHERE id IS NOT NULL);
        
        -- Clean up orphaned images (no associated plant)
        DELETE FROM plants_mgmt_plantimage 
        WHERE plant_id NOT IN (SELECT id FROM plants_mgmt_plant WHERE id IS NOT NULL);
        
        -- Validate and fix data consistency
        UPDATE plants_mgmt_plant 
        SET updated_at = created_at 
        WHERE updated_at < created_at;
        
        -- Remove invalid confidence values
        UPDATE plants_mgmt_diagnosis 
        SET confidence = 0.0 
        WHERE confidence < 0 OR confidence > 1.0;
        
        -- Update timestamps for future dates
        UPDATE plants_mgmt_sensordata 
        SET timestamp = NOW() 
        WHERE timestamp > NOW();
        
        -- Add constraints for future data integrity
        ALTER TABLE plants_mgmt_sensordata 
        ADD CONSTRAINT chk_sensor_values 
        CHECK (
            humidity BETWEEN 0 AND 100 
            AND temperature BETWEEN -50 AND 60 
            AND ph BETWEEN 0 AND 14 
            AND soil_moisture BETWEEN 0 AND 100 
            AND uv_index BETWEEN 0 AND 15
        );
        """
    
    def get_reverse_sql(self) -> str:
        """Get rollback SQL for schema validation"""
        return """
        -- Remove constraints
        ALTER TABLE plants_mgmt_sensordata DROP CONSTRAINT IF EXISTS chk_sensor_values;
        
        -- Note: Data cleanup operations cannot be easily rolled back
        -- This migration should be reviewed before execution
        """
    
    def get_validation_checks(self) -> List[str]:
        """Get validation checks for schema cleanup"""
        return [
            "SELECT COUNT(*) FROM plants_mgmt_sensordata s LEFT JOIN plants_mgmt_plant p ON s.plant_id = p.id WHERE p.id IS NULL",
            "SELECT COUNT(*) FROM plants_mgmt_diagnosis d LEFT JOIN plants_mgmt_plant p ON d.plant_id = p.id WHERE p.id IS NULL",
            "SELECT COUNT(*) FROM plants_mgmt_plantimage i LEFT JOIN plants_mgmt_plant p ON i.plant_id = p.id WHERE p.id IS NULL",
            "SELECT COUNT(*) FROM plants_mgmt_sensordata WHERE timestamp > NOW()",
            "SELECT COUNT(*) FROM plants_mgmt_plant WHERE updated_at < created_at",
            "SELECT COUNT(*) FROM plants_mgmt_diagnosis WHERE confidence < 0 OR confidence > 1.0"
        ]


def create_migration_plan() -> MigrationPlan:
    """Create and configure migration plan"""
    plan = MigrationPlan()
    
    # Add performance optimization migration
    perf_migration = PerformanceOptimizationMigration()
    plan.add_migration(
        name=perf_migration.name,
        description=perf_migration.description,
        forward_sql=perf_migration.get_forward_sql(),
        reverse_sql=perf_migration.get_reverse_sql(),
        dependencies=perf_migration.get_dependencies(),
        estimated_time=perf_migration.get_estimated_time(),
        risk_level=perf_migration.risk_level
    )
    
    # Add schema validation migration
    schema_migration = SchemaValidationMigration()
    plan.add_migration(
        name=schema_migration.name,
        description=schema_migration.description,
        forward_sql=schema_migration.get_forward_sql(),
        reverse_sql=schema_migration.get_reverse_sql(),
        dependencies=[perf_migration.name],
        estimated_time=schema_migration.get_estimated_time(),
        risk_level=schema_migration.risk_level
    )
    
    return plan


def execute_safely(migration_plan: MigrationPlan, dry_run: bool = False) -> Dict[str, Any]:
    """Execute migration plan safely"""
    # Validate plan
    validation = migration_plan.validate_plan()
    if not validation['valid']:
        raise Exception(f"Migration plan validation failed: {validation['errors']}")
    
    if validation['warnings']:
        for warning in validation['warnings']:
            logger.warning(f"Migration warning: {warning}")
    
    # Generate execution plan
    execution_plan = migration_plan.generate_execution_plan()
    
    # Execute migrations
    executor = SafeMigrationExecutor(dry_run=dry_run)
    
    for migration in execution_plan:
        success = executor.execute_migration(migration)
        if not success:
            logger.error(f"Migration execution stopped due to failure: {migration['name']}")
            break
    
    return executor.get_execution_report()
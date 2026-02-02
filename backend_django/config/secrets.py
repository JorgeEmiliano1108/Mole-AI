"""
Enterprise-grade secret management and credential security for Mole AI
Provides secure storage, rotation, and access control for secrets
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import hashlib
import secrets

logger = logging.getLogger('security.secrets')


class SecretManager:
    """
    Enterprise-grade secret manager with encryption and rotation support
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or self._get_or_create_master_key()
        self.cipher_suite = Fernet(self.master_key.encode())
        self.secrets_file = os.environ.get('SECRETS_FILE', '/etc/mole_ai/secrets.json')
        self.rotation_days = int(os.environ.get('SECRET_ROTATION_DAYS', '90'))
        
        # Ensure secrets directory exists
        os.makedirs(os.path.dirname(self.secrets_file), exist_ok=True)
        
        # Load existing secrets
        self._load_secrets()
    
    def _get_or_create_master_key(self) -> str:
        """Get or create master encryption key"""
        # Try to get from environment
        master_key = os.environ.get('MOLE_AI_MASTER_KEY')
        if master_key:
            return master_key
        
        # Try to get from file
        key_file = os.environ.get('MASTER_KEY_FILE', '/etc/mole_ai/.master_key')
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                return f.read().strip()
        
        # Generate new master key
        new_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        # Save to file with restricted permissions
        with open(key_file, 'w') as f:
            f.write(new_key)
        os.chmod(key_file, 0o600)  # Only owner can read/write
        
        logger.warning(f"Generated new master key. Save it securely: {key_file}")
        return new_key
    
    def _load_secrets(self):
        """Load encrypted secrets from file"""
        if os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file, 'r') as f:
                    encrypted_data = f.read()
                    
                if encrypted_data.strip():
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode()).decode()
                    self.secrets = json.loads(decrypted_data)
                else:
                    self.secrets = {}
                    
            except Exception as e:
                logger.error(f"Failed to load secrets: {e}")
                self.secrets = {}
        else:
            self.secrets = {}
    
    def _save_secrets(self):
        """Save encrypted secrets to file"""
        try:
            # Add metadata
            secrets_with_metadata = {
                'secrets': self.secrets,
                'metadata': {
                    'updated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'rotation_days': self.rotation_days
                }
            }
            
            # Encrypt and save
            json_data = json.dumps(secrets_with_metadata)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            with open(self.secrets_file, 'w') as f:
                f.write(encrypted_data.decode())
            
            # Set secure permissions
            os.chmod(self.secrets_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
            raise
    
    def store_secret(self, key: str, value: str, 
                   environment: str = 'production',
                   rotate_days: Optional[int] = None,
                   description: Optional[str] = None):
        """Store a secret with metadata"""
        try:
            secret_data = {
                'value': value,
                'environment': environment,
                'created_at': datetime.now().isoformat(),
                'rotate_days': rotate_days or self.rotation_days,
                'description': description or f"Secret for {key}",
                'last_rotated': None,
                'version': 1
            }
            
            self.secrets[key] = secret_data
            self._save_secrets()
            
            logger.info(f"Stored secret: {key}")
            
        except Exception as e:
            logger.error(f"Failed to store secret {key}: {e}")
            raise
    
    def get_secret(self, key: str, environment: str = 'production') -> Optional[str]:
        """Retrieve a secret if valid for environment"""
        try:
            if key not in self.secrets:
                logger.warning(f"Secret not found: {key}")
                return None
            
            secret_data = self.secrets[key]
            
            # Check environment
            if secret_data['environment'] != environment:
                logger.warning(f"Secret {key} not available for environment: {environment}")
                return None
            
            # Check rotation
            if self._needs_rotation(secret_data):
                logger.warning(f"Secret {key} needs rotation")
                self._rotate_secret(key)
            
            return secret_data['value']
            
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return None
    
    def _needs_rotation(self, secret_data: Dict[str, Any]) -> bool:
        """Check if secret needs rotation"""
        if secret_data.get('last_rotated') is None:
            # Check based on creation date
            created_at = datetime.fromisoformat(secret_data['created_at'])
            return datetime.now() > created_at + timedelta(days=secret_data['rotate_days'])
        
        # Check based on last rotation
        last_rotated = datetime.fromisoformat(secret_data['last_rotated'])
        return datetime.now() > last_rotated + timedelta(days=secret_data['rotate_days'])
    
    def _rotate_secret(self, key: str):
        """Rotate a secret"""
        try:
            old_secret_data = self.secrets[key]
            
            # Create new version
            new_secret_data = old_secret_data.copy()
            new_secret_data['last_rotated'] = datetime.now().isoformat()
            new_secret_data['version'] += 1
            
            # Store new secret (value would be generated externally)
            self.secrets[key] = new_secret_data
            self._save_secrets()
            
            logger.info(f"Rotated secret: {key} (version {new_secret_data['version']})")
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {key}: {e}")
            raise
    
    def list_secrets(self, environment: str = 'production', 
                   include_metadata: bool = False) -> Dict[str, Any]:
        """List all secrets for environment"""
        result = {}
        
        for key, secret_data in self.secrets.items():
            if secret_data['environment'] == environment:
                if include_metadata:
                    result[key] = secret_data
                else:
                    result[key] = {
                        'value': secret_data['value'],
                        'created_at': secret_data['created_at'],
                        'version': secret_data['version']
                    }
        
        return result
    
    def delete_secret(self, key: str):
        """Delete a secret"""
        try:
            if key in self.secrets:
                del self.secrets[key]
                self._save_secrets()
                logger.info(f"Deleted secret: {key}")
            else:
                logger.warning(f"Secret not found for deletion: {key}")
                
        except Exception as e:
            logger.error(f"Failed to delete secret {key}: {e}")
            raise
    
    def check_rotation_schedule(self) -> List[str]:
        """Check which secrets need rotation"""
        need_rotation = []
        
        for key, secret_data in self.secrets.items():
            if self._needs_rotation(secret_data):
                need_rotation.append(key)
        
        return need_rotation


class DatabaseCredentialManager:
    """
    Specialized manager for database credentials with secure access patterns
    """
    
    def __init__(self, secret_manager: SecretManager):
        self.secret_manager = secret_manager
        self.db_secrets_prefix = 'database_'
    
    def get_connection_string(self, service: str = 'default', environment: str = 'production') -> Optional[str]:
        """Get secure database connection string"""
        try:
            # Get individual credentials
            host = self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_host', environment)
            port = self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_port', environment)
            database = self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_database', environment)
            username = self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_username', environment)
            password = self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_password', environment)
            
            if not all([host, port, database, username, password]):
                raise ValueError(f"Missing database credentials for service: {service}")
            
            # Build secure connection string
            connection_string = (
                f"postgresql://{username}:{password}@{host}:{port}/{database}"
                f"?sslmode=require&sslcert=/etc/ssl/client-cert.pem"
                f"&sslkey=/etc/ssl/client-key.pem&sslrootcert=/etc/ssl/ca-cert.pem"
            )
            
            return connection_string
            
        except Exception as e:
            logger.error(f"Failed to get database connection string: {e}")
            return None
    
    def get_credentials_for_service(self, service: str, environment: str = 'production') -> Dict[str, str]:
        """Get database credentials for specific service"""
        return {
            'host': self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_host', environment) or '',
            'port': self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_port', environment) or '5432',
            'database': self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_database', environment) or '',
            'username': self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_username', environment) or '',
            'password': self.secret_manager.get_secret(f'{self.db_secrets_prefix}{service}_password', environment) or '',
            'ssl_mode': 'require',
            'connection_timeout': '30',
            'application_name': f'mole_ai_{service}'
        }


class APICredentialManager:
    """
    Manager for API keys and external service credentials
    """
    
    def __init__(self, secret_manager: SecretManager):
        self.secret_manager = secret_manager
        self.api_secrets_prefix = 'api_'
    
    def get_api_credentials(self, service: str, environment: str = 'production') -> Dict[str, str]:
        """Get API credentials for external service"""
        return {
            'api_key': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_key', environment) or '',
            'api_secret': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_secret', environment) or '',
            'endpoint': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_endpoint', environment) or '',
            'version': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_version', environment) or 'v1',
            'timeout': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_timeout', environment) or '30'
        }
    
    def get_oauth_credentials(self, service: str, environment: str = 'production') -> Dict[str, str]:
        """Get OAuth credentials for external service"""
        return {
            'client_id': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_client_id', environment) or '',
            'client_secret': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_client_secret', environment) or '',
            'redirect_uri': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_redirect_uri', environment) or '',
            'scope': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_scope', environment) or '',
            'token_url': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_token_url', environment) or '',
            'auth_url': self.secret_manager.get_secret(f'{self.api_secrets_prefix}{service}_auth_url', environment) or ''
        }


class SecurityAuditor:
    """
    Security auditor for credential access and usage
    """
    
    def __init__(self, log_file: str = '/var/log/mole_ai/security_audit.log'):
        self.log_file = log_file
        self.audit_events = []
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log_access(self, 
                  resource_type: str,
                  resource_name: str,
                  user: str,
                  action: str,
                  ip_address: str,
                  user_agent: str,
                  success: bool,
                  timestamp: Optional[datetime] = None):
        """Log access to security resources"""
        event = {
            'timestamp': timestamp or datetime.now().isoformat(),
            'resource_type': resource_type,  # database, api, file
            'resource_name': resource_name,
            'user': user,
            'action': action,  # read, write, delete, rotate
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success
        }
        
        self.audit_events.append(event)
        self._write_to_log(event)
        
        # Alert on suspicious activity
        if not success or action in ['delete', 'rotate']:
            logger.warning(f"SECURITY ALERT: {event}")
    
    def _write_to_log(self, event: Dict[str, Any]):
        """Write audit event to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_access_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get access report for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.audit_events 
            if datetime.fromisoformat(event['timestamp']) > cutoff_time
        ]
        
        # Generate report
        failed_attempts = [e for e in recent_events if not e['success']]
        suspicious_actions = [e for e in recent_events if e['action'] in ['delete', 'rotate']]
        
        return {
            'period_hours': hours,
            'total_accesses': len(recent_events),
            'failed_attempts': len(failed_attempts),
            'suspicious_actions': len(suspicious_actions),
            'unique_users': len(set(e['user'] for e in recent_events)),
            'resource_types': list(set(e['resource_type'] for e in recent_events)),
            'failed_attempts_detail': failed_attempts[-10:],  # Last 10 failures
            'suspicious_actions_detail': suspicious_actions
        }


class CredentialRotator:
    """
    Automated credential rotation manager
    """
    
    def __init__(self, secret_manager: SecretManager, auditor: SecurityAuditor):
        self.secret_manager = secret_manager
        self.auditor = auditor
        
    def rotate_database_credentials(self, service: str, new_credentials: Dict[str, str]):
        """Rotate database credentials for a service"""
        try:
            # Store new credentials
            for key, value in new_credentials.items():
                secret_key = f'database_{service}_{key}'
                self.secret_manager.store_secret(
                    key=secret_key,
                    value=value,
                    rotate_days=90,
                    description=f"Database {key} for {service}"
                )
            
            # Log rotation
            self.auditor.log_access(
                resource_type='database',
                resource_name=service,
                user='system_rotator',
                action='rotate',
                ip_address='127.0.0.1',
                user_agent='credential_rotator',
                success=True
            )
            
            logger.info(f"Successfully rotated database credentials for {service}")
            
        except Exception as e:
            logger.error(f"Failed to rotate database credentials for {service}: {e}")
            
            # Log failed rotation
            self.auditor.log_access(
                resource_type='database',
                resource_name=service,
                user='system_rotator',
                action='rotate',
                ip_address='127.0.0.1',
                user_agent='credential_rotator',
                success=False
            )
    
    def rotate_api_credentials(self, service: str, new_credentials: Dict[str, str]):
        """Rotate API credentials for a service"""
        try:
            # Store new credentials
            for key, value in new_credentials.items():
                secret_key = f'api_{service}_{key}'
                self.secret_manager.store_secret(
                    key=secret_key,
                    value=value,
                    rotate_days=60,
                    description=f"API {key} for {service}"
                )
            
            # Log rotation
            self.auditor.log_access(
                resource_type='api',
                resource_name=service,
                user='system_rotator',
                action='rotate',
                ip_address='127.0.0.1',
                user_agent='credential_rotator',
                success=True
            )
            
            logger.info(f"Successfully rotated API credentials for {service}")
            
        except Exception as e:
            logger.error(f"Failed to rotate API credentials for {service}: {e}")
            
            # Log failed rotation
            self.auditor.log_access(
                resource_type='api',
                resource_name=service,
                user='system_rotator',
                action='rotate',
                ip_address='127.0.0.1',
                user_agent='credential_rotator',
                success=False
            )


# Global instances
secret_manager = SecretManager()
db_credential_manager = DatabaseCredentialManager(secret_manager)
api_credential_manager = APICredentialManager(secret_manager)
security_auditor = SecurityAuditor()
credential_rotator = CredentialRotator(secret_manager, security_auditor)
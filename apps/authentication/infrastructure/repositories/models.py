from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    Integrates with Supabase authentication.
    """
    
    # Supabase specific fields
    supabase_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    supabase_role = models.CharField(max_length=50, default='authenticated')
    supabase_app_metadata = models.JSONField(default=dict, blank=True)
    supabase_user_metadata = models.JSONField(default=dict, blank=True)
    
    # Additional fields for Mole AI
    avatar_url = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'auth_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.email} ({self.supabase_uid})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_subscription(self):
        """Check if user has active premium subscription."""
        if not self.is_premium or not self.subscription_expires:
            return False
        from django.utils import timezone
        return self.subscription_expires > timezone.now()

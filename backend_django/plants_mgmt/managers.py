"""
Enterprise-grade query managers for optimized database access
Provides high-performance query patterns for Mole AI application
"""

from django.db import models
from django.db.models import Q, Count, Avg, Max, Min
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('database.performance')


class PlantManager(models.Manager):
    """Optimized manager for Plant queries"""
    
    def get_dashboard_data(self, user):
        """
        Optimized query for dashboard data with single database hit
        Returns plants with latest diagnosis and sensor data
        """
        return self.filter(owner=user)\
                  .select_related('owner')\
                  .prefetch_related(
                      models.Prefetch(
                          'diagnoses',
                          queryset=Diagnosis.objects.select_related('sensor_data')\
                                             .order_by('-created_at')[:1],
                          to_attr='latest_diagnosis'
                      ),
                      models.Prefetch(
                          'sensor_readings',
                          queryset=SensorData.objects.order_by('-timestamp')[:5],
                          to_attr='recent_sensors'
                      ),
                      models.Prefetch(
                          'images',
                          queryset=PlantImage.objects.order_by('-uploaded_at')[:3],
                          to_attr='recent_images'
                      )
                  )\
                  .annotate(
                      latest_diagnosis_time=Max('diagnoses__created_at'),
                      total_diagnoses=Count('diagnoses'),
                      last_sensor_time=Max('sensor_readings__timestamp'),
                      total_sensor_readings=Count('sensor_readings')
                  )\
                  .order_by('-created_at')
    
    def get_active_plants(self, user):
        """Get only active plants that need monitoring"""
        return self.filter(
            owner=user,
            status__in=['healthy', 'stress_water', 'pest_detection', 'nutrient_deficiency']
        ).select_related('owner')\
         .prefetch_related('sensor_readings', 'diagnoses')
    
    def get_plants_needing_attention(self, user):
        """Get plants that need immediate attention"""
        threshold_time = timezone.now() - timedelta(hours=24)
        
        return self.filter(
            owner=user
        ).filter(
            Q(status__in=['stress_water', 'pest_detection', 'multiple_issues']) |
            Q(sensor_readings__timestamp__lt=threshold_time) |
            Q(diagnoses__urgency_level__in=['high', 'critical'],
              diagnoses__created_at__gte=threshold_time)
        ).distinct()\
         .select_related('owner')\
         .prefetch_related(
             'diagnoses__sensor_data',
             'sensor_readings'
         )\
         .order_by('-updated_at')
    
    def get_plant_analytics(self, user, days=30):
        """
        Get analytics data for plants over specified period
        Optimized for reporting and analytics dashboards
        """
        start_date = timezone.now() - timedelta(days=days)
        
        return self.filter(owner=user, created_at__gte=start_date)\
                  .annotate(
                      avg_confidence=Avg('diagnoses__confidence'),
                      high_urgency_count=Count(
                          'diagnoses',
                          filter=Q(diagnoses__urgency_level__in=['high', 'critical'])
                      ),
                      total_diagnoses=Count('diagnoses'),
                      days_active=ExtractDay('created_at')
                  )\
                  .values(
                      'plant_type',
                      'status',
                      'avg_confidence',
                      'high_urgency_count',
                      'total_diagnoses',
                      'days_active'
                  )\
                  .order_by('-total_diagnoses')


class SensorDataManager(models.Manager):
    """Optimized manager for SensorData queries"""
    
    def get_recent_data(self, plant_id, hours=24, limit=100):
        """Get recent sensor data with optimized pagination"""
        threshold_time = timezone.now() - timedelta(hours=hours)
        
        return self.filter(
            plant_id=plant_id,
            timestamp__gte=threshold_time
        ).select_related('plant', 'plant__owner')\
         .order_by('-timestamp')[:limit]
    
    def get_sensor_analytics(self, plant_id, days=7):
        """Get analytics for sensor data over time period"""
        start_date = timezone.now() - timedelta(days=days)
        
        return self.filter(
            plant_id=plant_id,
            timestamp__gte=start_date
        ).aggregate(
            avg_humidity=Avg('humidity'),
            avg_temperature=Avg('temperature'),
            avg_ph=Avg('ph'),
            avg_uv_index=Avg('uv_index'),
            avg_soil_moisture=Avg('soil_moisture'),
            max_temperature=Max('temperature'),
            min_temperature=Min('temperature'),
            max_humidity=Max('humidity'),
            min_humidity=Min('humidity'),
            reading_count=Count('id'),
            latest_reading=Max('timestamp')
        )
    
    def get_alert_conditions(self, plant_id=None):
        """Get sensors currently in alert condition"""
        alert_query = Q(
            humidity__lt=30
        ) | Q(
            temperature__gt=35
        ) | Q(
            soil_moisture__lt=20
        ) | Q(
            ph__lt=5.5
        ) | Q(
            ph__gt=7.5
        ) | Q(
            uv_index__gt=10
        )
        
        queryset = self.filter(alert_query)\
                     .select_related('plant', 'plant__owner')\
                     .order_by('-timestamp')
        
        if plant_id:
            queryset = queryset.filter(plant_id=plant_id)
        
        return queryset[:50]  # Limit to recent alerts
    
    def get_time_series_data(self, plant_id, days=7, interval='hour'):
        """
        Get time series data for charts and monitoring
        Optimized for dashboard visualization
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Use PostgreSQL's time_bucket function if available
        if interval == 'hour':
            time_bucket = "date_trunc('hour', timestamp)"
        elif interval == 'day':
            time_bucket = "date_trunc('day', timestamp)"
        else:
            time_bucket = "date_trunc('hour', timestamp)"
        
        return self.filter(
            plant_id=plant_id,
            timestamp__gte=start_date
        ).extra({
            'time_bucket': time_bucket
        }).values('time_bucket')\
         .annotate(
             avg_humidity=Avg('humidity'),
             avg_temperature=Avg('temperature'),
             avg_ph=Avg('ph'),
             avg_soil_moisture=Avg('soil_moisture'),
             reading_count=Count('id')
         )\
         .order_by('time_bucket')


class DiagnosisManager(models.Manager):
    """Optimized manager for Diagnosis queries"""
    
    def get_urgent_diagnoses(self, user=None, hours=24):
        """Get urgent diagnoses requiring immediate attention"""
        threshold_time = timezone.now() - timedelta(hours=hours)
        
        queryset = self.filter(
            urgency_level__in=['high', 'critical'],
            created_at__gte=threshold_time
        ).select_related('plant', 'sensor_data', 'plant__owner')\
         .prefetch_related('plant__images')\
         .order_by('-created_at')
        
        if user:
            queryset = queryset.filter(plant__owner=user)
        
        return queryset
    
    def get_diagnosis_trends(self, user, days=30):
        """Get diagnosis trends for analytics dashboard"""
        start_date = timezone.now() - timedelta(days=days)
        
        return self.filter(
            plant__owner=user,
            created_at__gte=start_date
        ).extra({
            'day': "date_trunc('day', created_at)"
        }).values('day', 'urgency_level')\
         .annotate(
             diagnosis_count=Count('id'),
             avg_confidence=Avg('confidence')
         )\
         .order_by('-day')
    
    def get_performance_metrics(self, days=7):
        """Get AI model performance metrics"""
        start_date = timezone.now() - timedelta(days=days)
        
        return self.filter(
            created_at__gte=start_date,
            processing_time__isnull=False
        ).aggregate(
            avg_processing_time=Avg('processing_time'),
            max_processing_time=Max('processing_time'),
            min_processing_time=Min('processing_time'),
            avg_confidence=Avg('confidence'),
            total_diagnoses=Count('id'),
            urgent_diagnoses=Count(
                'id',
                filter=Q(urgency_level__in=['high', 'critical'])
            ),
            model_distribution=Count('ai_model_version')
        )
    
    def search_by_symptoms(self, search_query, user=None):
        """
        Full-text search in diagnosis data
        Optimized for symptom search functionality
        """
        queryset = self.annotate(
            search_vector=SearchVector(
                'diagnosis_text',
                'treatment_plan',
                'recommendations'
            )
        ).filter(search_vector=search_query)\
         .select_related('plant', 'plant__owner')\
         .order_by('-created_at', '-confidence')
        
        if user:
            queryset = queryset.filter(plant__owner=user)
        
        return queryset


class PlantImageManager(models.Manager):
    """Optimized manager for PlantImage queries"""
    
    def get_recent_images(self, plant_id, limit=10):
        """Get recent images for a plant"""
        return self.filter(
            plant_id=plant_id
        ).select_related('plant')\
         .order_by('-uploaded_at')[:limit]
    
    def get_images_by_type(self, plant_id, image_type):
        """Get images filtered by type (RGB/Infrared)"""
        return self.filter(
            plant_id=plant_id,
            image_type=image_type
        ).select_related('plant')\
         .order_by('-uploaded_at')
    
    def get_analysis_summary(self, plant_id, days=30):
        """Get summary of image analysis results"""
        start_date = timezone.now() - timedelta(days=days)
        
        return self.filter(
            plant_id=plant_id,
            uploaded_at__gte=start_date
        ).aggregate(
            total_images=Count('id'),
            rgb_images=Count('id', filter=Q(image_type='rgb')),
            infrared_images=Count('id', filter=Q(image_type='infrared')),
            latest_rgb=Max('uploaded_at', filter=Q(image_type='rgb')),
            latest_infrared=Max('uploaded_at', filter=Q(image_type='infrared')),
            avg_analysis_confidence=Avg(
                Cast(
                    KeyTransform('confidence', 'analysis_result'),
                    models.FloatField()
                )
            )
        )


class KnowledgeDocumentManager(models.Manager):
    """Optimized manager for KnowledgeDocument queries"""
    
    def search_documents(self, query, plant_types=None, limit=20):
        """
        Full-text search with plant type filtering
        Optimized for RAG knowledge base
        """
        queryset = self.filter(is_active=True)\
                     .annotate(
                         search_vector=SearchVector(
                             'title',
                             'content',
                             'tags'
                         )
                     )\
                     .filter(search_vector=query)
        
        if plant_types:
            # Convert plant types list to database query
            plant_type_q = Q()
            for plant_type in plant_types:
                plant_type_q |= Q(plant_types__icontains=plant_type)
            queryset = queryset.filter(plant_type_q)
        
        return queryset.select_related()\
                   .order_by('-created_at')[:limit]
    
    def get_documents_by_plant_type(self, plant_type):
        """Get documents relevant to specific plant type"""
        return self.filter(
            is_active=True,
            plant_types__icontains=plant_type
        ).order_by('-created_at')
    
    def get_popular_documents(self, limit=10):
        """Get most referenced/popular documents"""
        # This would need custom logic to track document usage
        return self.filter(is_active=True)\
                   .order_by('-created_at')[:limit]


# Custom QuerySet for advanced operations
class PlantQuerySet(models.QuerySet):
    """Custom QuerySet for Plant model with advanced operations"""
    
    def with_health_status(self):
        """Annotate with current health status"""
        return self.annotate(
            latest_diagnosis=Subquery(
                Diagnosis.objects.filter(plant=models.OuterRef('pk'))\
                              .order_by('-created_at')\
                              .values('urgency_level')[:1]
            ),
            last_sensor_check=Subquery(
                SensorData.objects.filter(plant=models.OuterRef('pk'))\
                              .order_by('-timestamp')\
                              .values('timestamp')[:1]
            )
        )
    
    def needing_attention(self):
        """Filter plants that need attention"""
        threshold_time = timezone.now() - timedelta(hours=24)
        return self.filter(
            Q(status__in=['stress_water', 'pest_detection', 'multiple_issues']) |
            Q(last_sensor_check__lt=threshold_time)
        )


# Import these at the bottom to avoid circular imports
from django.contrib.postgres.search import SearchVector
from django.db.models import Subquery, ExtractDay, KeyTransform, Cast
from .models import Diagnosis, SensorData, PlantImage
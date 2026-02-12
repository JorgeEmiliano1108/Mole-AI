"""
Application services for Core module.

Contains use cases and business logic orchestration.
These services coordinate between domain entities and infrastructure.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from ..domain.entities import (
    SensorReading, 
    PlantDiagnostic, 
    SensorType,
    SeverityLevel
)


class SensorAnalysisService:
    """Service for analyzing sensor data and detecting anomalies."""
    
    def analyze_trend(self, readings: List[SensorReading]) -> dict:
        """Analyze trends in sensor readings."""
        if not readings:
            return {"trend": "no_data", "anomaly_detected": False}
        
        values = [r.value for r in readings]
        if len(values) < 2:
            return {"trend": "insufficient_data", "anomaly_detected": False}
        
        # Simple trend detection
        recent_avg = sum(values[-3:]) / min(3, len(values))
        overall_avg = sum(values) / len(values)
        
        trend = "stable"
        if recent_avg > overall_avg * 1.2:
            trend = "increasing"
        elif recent_avg < overall_avg * 0.8:
            trend = "decreasing"
        
        # Anomaly detection
        anomaly_detected = any(r.is_critical() for r in readings[-5:])
        
        return {
            "trend": trend,
            "anomaly_detected": anomaly_detected,
            "recent_average": recent_avg,
            "overall_average": overall_avg
        }
    
    def predict_maintenance_need(self, readings: List[SensorReading]) -> Optional[str]:
        """Predict maintenance needs based on sensor patterns."""
        critical_readings = [r for r in readings if r.is_critical()]
        
        if len(critical_readings) >= 3:
            return "immediate_maintenance_required"
        elif len(critical_readings) >= 1:
            return "schedule_inspection"
        
        return None


class DiagnosticPrioritizationService:
    """Service for prioritizing plant diagnostics."""
    
    def prioritize_diagnostics(self, diagnostics: List[PlantDiagnostic]) -> List[PlantDiagnostic]:
        """Sort diagnostics by priority."""
        def priority_score(diagnostic: PlantDiagnostic) -> int:
            score = 0
            
            # Severity-based scoring
            severity_scores = {
                SeverityLevel.CRITICAL: 100,
                SeverityLevel.HIGH: 75,
                SeverityLevel.MEDIUM: 50,
                SeverityLevel.LOW: 25
            }
            score += severity_scores.get(diagnostic.severity, 0)
            
            # Confidence score influence
            score += diagnostic.confidence_score * 20
            
            # Immediate action bonus
            if diagnostic.requires_immediate_action():
                score += 50
            
            return int(score)
        
        return sorted(diagnostics, key=priority_score, reverse=True)
    
    def get_actionable_diagnostics(self, diagnostics: List[PlantDiagnostic]) -> List[PlantDiagnostic]:
        """Filter diagnostics that need immediate action."""
        return [
            d for d in diagnostics 
            if d.requires_immediate_action() or d.confidence_score > 0.8
        ]


class PlantMonitoringService:
    """Service for comprehensive plant monitoring."""
    
    def __init__(self):
        self.sensor_analysis = SensorAnalysisService()
        self.diagnostic_prioritization = DiagnosticPrioritizationService()
    
    def get_plant_status_summary(self, 
                                sensor_readings: List[SensorReading],
                                diagnostics: List[PlantDiagnostic]) -> dict:
        """Generate comprehensive plant status summary."""
        
        # Analyze sensors by type
        sensor_analysis = {}
        for sensor_type in SensorType:
            type_readings = [r for r in sensor_readings if r.sensor_type == sensor_type]
            sensor_analysis[sensor_type.value] = self.sensor_analysis.analyze_trend(type_readings)
        
        # Prioritize diagnostics
        prioritized_diagnostics = self.diagnostic_prioritization.prioritize_diagnostics(diagnostics)
        actionable_diagnostics = self.diagnostic_prioritization.get_actionable_diagnostics(diagnostics)
        
        # Overall health score
        health_score = self._calculate_health_score(sensor_readings, diagnostics)
        
        return {
            "health_score": health_score,
            "sensor_analysis": sensor_analysis,
            "total_diagnostics": len(diagnostics),
            "actionable_diagnostics": len(actionable_diagnostics),
            "critical_issues": len([d for d in diagnostics if d.severity == SeverityLevel.CRITICAL]),
            "last_updated": datetime.now(),
            "recommendations": self._generate_recommendations(sensor_analysis, actionable_diagnostics)
        }
    
    def _calculate_health_score(self, 
                               readings: List[SensorReading], 
                               diagnostics: List[PlantDiagnostic]) -> float:
        """Calculate overall plant health score (0-100)."""
        # Base score
        score = 100.0
        
        # Deductions for critical readings
        critical_readings = len([r for r in readings if r.is_critical()])
        score -= critical_readings * 10
        
        # Deductions for diagnostics
        for diagnostic in diagnostics:
            if diagnostic.severity == SeverityLevel.CRITICAL:
                score -= 20
            elif diagnostic.severity == SeverityLevel.HIGH:
                score -= 10
            elif diagnostic.severity == SeverityLevel.MEDIUM:
                score -= 5
        
        # Confidence adjustments
        if diagnostics:
            avg_confidence = sum(d.confidence_score for d in diagnostics) / len(diagnostics)
            score *= avg_confidence
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(self, 
                                sensor_analysis: dict, 
                                actionable_diagnostics: List[PlantDiagnostic]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Sensor-based recommendations
        for sensor_type, analysis in sensor_analysis.items():
            if analysis.get("anomaly_detected"):
                recommendations.append(f"Investigate {sensor_type} sensor anomalies")
        
        # Diagnostic-based recommendations
        for diagnostic in actionable_diagnostics[:3]:  # Top 3
            if diagnostic.requires_immediate_action():
                recommendations.append(f"URGENT: Address {diagnostic.condition_name}")
        
        return recommendations
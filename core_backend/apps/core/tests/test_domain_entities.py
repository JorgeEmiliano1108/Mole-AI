from django.test import TestCase

from apps.core.domain.entities import (
    DiagnosticRecommendation,
    DiagnosticType,
    PlantDiagnostic,
    PlantKnowledge,
    SensorReading,
    SeverityLevel,
)


def _diag(sev, recs=None):
    return PlantDiagnostic(
        plant_id='p', diagnostic_type=DiagnosticType.DISEASE,
        condition_name='c', condition_description='d', severity=sev,
        ai_model_used='m', confidence_score=0.9,
        recommendations=recs or [], treatment_protocol='t')


class EntitiesTests(TestCase):
    def test_severity_levels(self):
        self.assertEqual(SeverityLevel.CRITICAL.value, 'critical')
        self.assertEqual(DiagnosticType.PEST_INFESTATION.value, 'pest_infestation')

    def test_sensor_reading_critical(self):
        self.assertTrue(SensorReading(plant_id='p', air_temperature=40).is_critical())
        self.assertTrue(SensorReading(plant_id='p', air_temperature=0).is_critical())
        self.assertTrue(SensorReading(plant_id='p', soil_humidity=5).is_critical())
        self.assertTrue(SensorReading(plant_id='p', soil_humidity=95).is_critical())
        self.assertTrue(SensorReading(plant_id='p', ph_level=3.0).is_critical())
        self.assertTrue(SensorReading(plant_id='p', ph_level=10.0).is_critical())
        self.assertFalse(SensorReading(plant_id='p', air_temperature=22,
                                       soil_humidity=50, ph_level=6.5).is_critical())
        self.assertFalse(SensorReading(plant_id='p').is_critical())

    def test_plant_knowledge_reliable(self):
        k = PlantKnowledge(title='t', content='c', plant_species='s',
                           plant_genus='g', plant_family='f',
                           common_names=['a'], confidence_score=0.8)
        self.assertTrue(k.is_reliable())
        k2 = PlantKnowledge(title='t', content='c', plant_species='s',
                            plant_genus='g', plant_family='f', common_names=[],
                            confidence_score=0.5)
        self.assertFalse(k2.is_reliable())

    def test_diagnostic_priority_and_action(self):
        crit = _diag(SeverityLevel.CRITICAL, [DiagnosticRecommendation(
            action='a', priority='high', timeline='t', resources_needed=[])])
        low = _diag(SeverityLevel.LOW)
        self.assertTrue(crit.requires_immediate_action())
        self.assertTrue(_diag(SeverityLevel.HIGH).requires_immediate_action())
        self.assertFalse(low.requires_immediate_action())
        self.assertEqual(len(crit.get_priority_recommendations()), 1)
        self.assertEqual(low.get_priority_recommendations(), [])

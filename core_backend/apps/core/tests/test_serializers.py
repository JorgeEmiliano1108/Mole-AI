import time

from django.test import TestCase

from apps.core.serializers import EdgeFrameSerializer, LLMChatRequestSerializer


class SerializersTests(TestCase):
    def test_edge_frame_valid(self):
        s = EdgeFrameSerializer(data={
            'ts': time.time() - 60, 'ri': 5,
            'a': {'t': 22.5, 'h': 60.0}, 's': [{'p': '32', 'v': 1800}]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['a']['air_temperature'], 22.5)

    def test_edge_frame_future_rejected(self):
        s = EdgeFrameSerializer(data={'ts': time.time() + 3600})
        self.assertFalse(s.is_valid())
        self.assertIn('ts', s.errors)

    def test_edge_frame_out_of_range(self):
        s = EdgeFrameSerializer(data={'ts': time.time(), 'a': {'t': 200.0}})
        self.assertFalse(s.is_valid())

    def test_edge_frame_defaults(self):
        s = EdgeFrameSerializer(data={'ts': time.time()})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['ri'], 5)
        self.assertEqual(s.validated_data['s'], [])

    def test_llm_prompt_rules(self):
        ok = LLMChatRequestSerializer(data={'prompt': '¿riego?'})
        self.assertTrue(ok.is_valid(), ok.errors)
        bad = LLMChatRequestSerializer(data={'prompt': 'x'})
        self.assertFalse(bad.is_valid())
        empty = LLMChatRequestSerializer(data={'prompt': '   '})
        self.assertFalse(empty.is_valid())

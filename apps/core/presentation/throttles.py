from rest_framework.throttling import UserRateThrottle

class LLMChatThrottle(UserRateThrottle):
    scope = 'llm_chat'

class DiagnosticsThrottle(UserRateThrottle):
    scope = 'diagnostics'

class SensorDataThrottle(UserRateThrottle):
    scope = 'sensor_data'
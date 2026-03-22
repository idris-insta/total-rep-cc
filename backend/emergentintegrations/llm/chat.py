"""Stub for emergentintegrations LLM chat module"""

class UserMessage:
    def __init__(self, text: str = ""):
        self.text = text

class LlmChat:
    def __init__(self, *args, **kwargs):
        pass

    async def send_message(self, message, *args, **kwargs):
        return "AI insights are not available - LLM service not configured."

    def send_message_sync(self, message, *args, **kwargs):
        return "AI insights are not available - LLM service not configured."

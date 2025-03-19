# Updated llm_client.py
import openai
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
    async def generate_stream(self, prompt):
        """Stream response from OpenAI using official async API"""
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
            {"role": "system", "content": "Follow these instructions in all your responses:\n1. Use English language only;\n2. Do not use any other language except English;\n3. Translate any input to English first before processing it;\n4. Always respond in English regardless of the input language."},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        max_tokens=150,
        temperature=0.7
    )
        
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

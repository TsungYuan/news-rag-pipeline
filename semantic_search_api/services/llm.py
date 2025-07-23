import logging
import google.generativeai as genai
import os
import json
from promtps.summarize_news_prompt import SUMMARIZE_NEWS_PROMPT
from typing import List, Dict

logger = logging.getLogger(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

def build_prompt(query: str, results: List[Dict]) -> str:
    return SUMMARIZE_NEWS_PROMPT.format(
        query=query,
        results=results
    )

def call_gemini(prompt: str) -> str:
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)


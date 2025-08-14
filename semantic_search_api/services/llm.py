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
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        if not response.text:
            logger.error(
                f"Gemini API returned an empty response. "
                f"finish_reason: {response.candidates[0].finish_reason}"
            )
            return {
                "summary": "很抱歉，我無法處理您的請求，請稍後再試。",
                "references": []
            }

        return json.loads(response.text)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}. Response text: {response.text}")
        return {
            "summary": "很抱歉，模型返回了無法解析的資料。請稍後再試。",
            "references": []
        }
    except Exception as e:
        logger.error(f"An error occurred while calling Gemini: {e}")
        return {
            "summary": "很抱歉，與模型通訊時發生錯誤。請稍後再試。",
            "references": []
        }


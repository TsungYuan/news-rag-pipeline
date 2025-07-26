import google.generativeai as genai
import json
import logging
import time

logger = logging.getLogger(__name__)

class GeminiNewsClassifier:
    """
    A class to handle news classification using the Google Gemini API.
    """
    def __init__(self, api_key: str, categories: list[str], model_name: str = "gemini-2.5-pro"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.categories = categories
        self.batch_prompt_template = f"""
        你是一位專業的新聞編輯，你的任務是根據以下提供的一系列新聞摘要，為每一則摘要分類。
        請從以下類別中選擇一個：
        [{', '.join(self.categories)}]
        你必須嚴格按照 JSON 格式回傳結果。回傳的結果應該是一個 JSON 陣列，陣列中的每個物件都包含 "id" 和 "category" 兩個鍵。
        輸入: {{batch_of_summaries_in_json}}
        """

    def classify_news_batch(self, news_batch: list[dict]) -> list[dict]:
        """
        Classifies a batch of news articles using the Gemini model.

        Args:
            news_batch: A list of dictionaries, each containing 'news_id', 'title', 'summary'.

        Returns:
            A list of dictionaries, each with 'id' and 'category'.
        """
        if not news_batch:
            logger.info("No news in batch to classify.")
            return []

        summaries_for_prompt = []
        for item in news_batch:
            text_part = []
            if item.get("title"):
                text_part.append(f"標題：{item['title']}")
            if item.get("summary"):
                text_part.append(f"摘要：{item['summary']}")
            combined_text = "; ".join(text_part) or "無資料"
            summaries_for_prompt.append({
                "id": item["news_id"],
                "summary": combined_text
            })

        summaries_json_string = json.dumps(summaries_for_prompt, ensure_ascii=False, indent=2)
        prompt = self.batch_prompt_template.format(batch_of_summaries_in_json=summaries_json_string)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                ),
                request_options={"timeout": 120} # Add timeout for API request
            )
            if not response.text:
                logger.warning(f"Gemini API returned empty response for batch. Prompt: {prompt[:200]}...")
                return [{"id": item["news_id"], "category": "Classification_Failed"} for item in news_batch]

            batch_result = json.loads(response.text)
            logger.info(f"Classified {len(batch_result)} news items.")
            return batch_result
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON decode error from Gemini response: {json_err}. Response text: {response.text}")
            return [{"id": item["news_id"], "category": "JSON_Parse_Error"} for item in news_batch]
        except Exception as e:
            logger.error(f"Error classifying news batch with Gemini: {e}. Prompt: {prompt[:200]}...")
            # Return a default category for failed items to allow pipeline to continue
            return [{"id": item["news_id"], "category": "API_Error"} for item in news_batch]
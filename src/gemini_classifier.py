import google.generativeai as genai
import json
import logging
import time

logger = logging.getLogger(__name__)

class GeminiNewsClassifier:
    """
    A class to handle news classification using the Google Gemini API.
    """
    def __init__(self, api_key: str, categories: list[str], model_name: str = "gemini-2.5-pro", batch_size: int = 15):
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.categories = categories
        self.batch_size = batch_size
        self.batch_prompt_template = f"""
        你是一位專業的新聞編輯，你的任務是根據以下提供的一系列新聞標題及摘要，為每一則摘要分類。
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

        classified_results = []
        for i in range(0, len(news_batch), self.batch_size):
            sub_batch = news_batch[i:i + self.batch_size]
            print(f"sub_batch size: {len(sub_batch)}")

            summaries_for_prompt = []
            for item in sub_batch:
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

            retries = 3
            for attempt in range(retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            response_mime_type="application/json"
                        ),
                        request_options={"timeout": 120}
                    )
                    if not response.text:
                        logger.warning(f"Gemini API returned empty response for sub-batch. Retrying...")
                        if attempt < retries - 1:
                            time.sleep(5)
                            continue
                        else:
                            logger.error(f"Failed after {retries} retries. Prompt: {prompt[:200]}...")
                            raise RuntimeError("Gemini API returned empty response repeatedly.")

                    sub_batch_result = json.loads(response.text)
                    logger.info(f"Classified {len(sub_batch_result)} news items.")
                    classified_results.extend(sub_batch_result) 
                    break

                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON decode error from Gemini response: {json_err}. Response text: {response.text}")
                    sub_batch_failed = [{"id": item["news_id"], "category": "JSON_Parse_Error"} for item in sub_batch]
                    classified_results.extend(sub_batch_failed)
                    break

                except Exception as e:
                    logger.error(f"Error classifying news sub-batch with Gemini on attempt {attempt + 1}: {e}. Prompt: {prompt[:200]}...")
                    if attempt < retries - 1:
                        time.sleep(5)
                        logger.info(f"Start {attempt + 2} attempt.")
                        continue
                    else:
                        logger.error(f"Failed after {retries} retries.")
                        sub_batch_failed = [{"id": item["news_id"], "category": "API_Error"} for item in sub_batch]
                        classified_results.extend(sub_batch_failed)
                        break
        logger.info(f"Total classified {len(classified_results)} news items.")
        return classified_results
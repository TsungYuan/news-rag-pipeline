import gradio as gr
import requests
import json
import pandas as pd
import os
from datetime import date, datetime, timedelta

API_BASE_URL = os.getenv("API_BASE_URL")

def query_api(user_input, chat_history):
    payload = {"query": user_input}
    try:
        response = requests.post(f"{API_BASE_URL}/rag_agent", json=payload)
        response.raise_for_status()
        full_response_data = response.json()

        answer = full_response_data.get("answer", {})
        summary = answer.get("summary", "根據目前的新聞內容，無法準確回答此問題。")
        llm_references = answer.get("references", [])
        retrieved_chunks_from_api = full_response_data.get("results", [])

        link_map = {}
        for _, raw_data in enumerate(retrieved_chunks_from_api):
            chunk_news_id = raw_data.get("news_id")
            url = raw_data.get("link", "#")

            if chunk_news_id is not None and url:
                link_map[str(chunk_news_id)] = url
        # print(link_map)

        chat_output = summary
        if llm_references:
            refs_str = "\n\n**參考資料：**\n"
            for ref in llm_references:
                news_id = ref.get("news_id", "")
                title = ref.get("title", "未知標題")
                publisher = ref.get("publisher", "未知來源")
                found_link = link_map.get(str(news_id), "#")

                refs_str += f"- [{title}]({found_link}) - {publisher}\n"
            chat_output += refs_str
        # print(chat_output)
                

        print(chat_output)
    
        return chat_output, full_response_data

    except Exception as e:
        return f"Error: {str(e)}"
    
def display_raw_json(raw_json_string):
    return json.loads(raw_json_string)

def get_top_categories_from_api(start_date_obj: datetime, end_date_obj: datetime, limit: int = 5):
    params = {}
    if start_date_obj:
        params["start_date"] = start_date_obj.strftime("%Y-%m-%d")
    if end_date_obj:
        params["end_date"] = end_date_obj.strftime("%Y-%m-%d")
    params["limit"] = limit

    try:
        response = requests.get(f"{API_BASE_URL}/top_categories", params=params)
        response.raise_for_status()
        data = response.json()
        
        
        categories = [item['category'] for item in data['top_categories']]
        counts = [item['count'] for item in data['top_categories']]

        plot_data = pd.DataFrame(
            {
                "Category": categories,
                "Count": counts
            }
        )
        
        return plot_data, f"{data.get('total_news_in_range', 0)} was published from {data.get('start_date', '所有時間')} to {data.get('end_date', '所有時間')}."

    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch top categories: {str(e)}"
        print(error_msg)
        return {
            "x": ["Error"],
            "y": [0],
            "type": "bar"
        }, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        return {
            "x": ["Error"],
            "y": [0],
            "type": "bar"
        }, error_msg
    
def get_top_publishers_from_api(start_date_obj: datetime, end_date_obj: datetime, limit: int = 5):
    params = {}
    if start_date_obj:
        params["start_date"] = start_date_obj.strftime("%Y-%m-%d")
    if end_date_obj:
        params["end_date"] = end_date_obj.strftime("%Y-%m-%d")
    params["limit"] = limit

    try:
        response = requests.get(f"{API_BASE_URL}/top_publishers", params=params)
        response.raise_for_status()
        data = response.json()
        
        
        publishers = [item['publisher'] for item in data['top_publishers']]
        counts = [item['count'] for item in data['top_publishers']]

        plot_data = pd.DataFrame(
            {
                "Publisher": publishers,
                "Count": counts
            }
        )
        
        return plot_data, data.get('total_news_in_range', 0)

    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch top publishers: {str(e)}"
        print(error_msg)
        return {
            "x": ["Error"],
            "y": [0],
            "type": "bar"
        }, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        return {
            "x": ["Error"],
            "y": [0],
            "type": "bar"
        }, error_msg


def perform_analytics(start_date_obj: datetime, end_date_obj: datetime, limit: int):
    category_df, category_info_text = get_top_categories_from_api(start_date_obj, end_date_obj, limit)
    publisher_df, publisher_total_news_count = get_top_publishers_from_api(start_date_obj, end_date_obj, limit)

    combined_info_text = category_info_text 

    return category_df, publisher_df, combined_info_text

with gr.Blocks(title="Taiwan News Agent") as tabs:
    current_raw_json_state = gr.State(value="{}")

    with gr.Tab("Chat"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("# Taiwan News Agent")
                chat_interface = gr.ChatInterface(
                    fn=query_api, 
                    additional_outputs=[current_raw_json_state] 
                )
            with gr.Column(scale=1):
                gr.Markdown("# API Raw Data")
                json_display_component = gr.JSON(
                    label="raw_data",
                    value=current_raw_json_state.value
                )
                current_raw_json_state.change(
                    fn=lambda x: x,
                    inputs=[current_raw_json_state],
                    outputs=[json_display_component],
                    queue=False
                )

        gr.HTML("<hr>")

        gr.Markdown("# News Trend Analytics")
        with gr.Row():
            with gr.Column(scale=1):
                start_date_picker = gr.DateTime(
                    label="Start Date",
                    value=datetime.combine(date.today() - timedelta(days=1), datetime.min.time()),
                    type="datetime",
                    include_time=False
                )
                end_date_picker = gr.DateTime(
                    label="End Date",
                    value=datetime.combine(date.today(), datetime.max.time()),
                    type="datetime",
                    include_time=False
                )
                limit_slider = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Top N"
                )
                analyze_btn = gr.Button("run")
            with gr.Column(scale=3):
                category_bar_chart = gr.BarPlot(
                    label="News Categories Distribution",
                    x="Category", 
                    y="Count", 
                    x_as_category=True,
                    height=400,
                    sort="-y"
                )
                analytics_info_text = gr.Markdown("click 'run' to show results.")
            with gr.Column(scale=3):
                publisher_bar_chart = gr.BarPlot(
                    label="News Publishers Distribution",
                    x="Publisher", 
                    y="Count", 
                    x_as_publisher=True,
                    height=400,
                    sort="-y"
                )

        analyze_btn.click(
            fn=perform_analytics,
            inputs=[start_date_picker, end_date_picker, limit_slider],
            outputs=[category_bar_chart, publisher_bar_chart, analytics_info_text],
            queue=False
        )

tabs.launch(server_name="0.0.0.0", server_port=7860, debug=True)
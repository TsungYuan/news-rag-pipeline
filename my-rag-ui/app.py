import gradio as gr
import requests
import json

API_URL = "http://semantic-api:8000/rag_agent"

def query_api(user_input, chat_history):
    payload = {"query": user_input}
    try:
        response = requests.post(API_URL, json=payload)
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

tabs.launch(server_name="0.0.0.0", server_port=7860, debug=True)
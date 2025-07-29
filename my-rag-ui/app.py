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
        references = full_response_data.get("results", [])

        if references:
            refs_str = "\n\n**參考資料：**\n" + "\n"
            for _, ref in enumerate(references):
                title = ref.get("meta_data", {}).get("title", "未知標題")
                publisher = ref.get("meta_data", {}).get("publisher", "未知來源")
                url = ref.get("link", "#")
                refs_str += f"- [{title}]({url}) - {publisher}\n"
            chat_output =  summary + refs_str

        return chat_output, full_response_data

    except Exception as e:
        return f"Error: {str(e)}"
    
def display_raw_json(raw_json_string):
    return json.loads(raw_json_string)
    
# def raw_json(user_input):
#     payload = {"query": user_input}
#     try:
#         response = requests.post(API_URL, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         return data.get("answer", {}), data.get("results", [])
#         # return data.dumps(data, indent=2, ensure_ascii=False)
#     except Exception as e:
#         return f"Error: {str(e)}"

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

tabs.launch(server_name="0.0.0.0", server_port=7860)
import gradio as gr
import requests

API_URL = "http://semantic-api:8000/rag_agent"

def query_api(user_input, history):
    payload = {"query": user_input}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer", {})
        summary = answer.get("summary", "根據目前的新聞內容，無法準確回答此問題。")
        references = data.get("results", [])

        if references:
            refs_str = "\n\n**參考資料：**\n" + "\n"
            for _, ref in enumerate(references):
                title = ref.get("meta_data", {}).get("title", "未知標題")
                publisher = ref.get("meta_data", {}).get("publisher", "未知來源")
                url = ref.get("link", "#")
                refs_str += f"- [{title}]({url}) - {publisher}\n"
            return summary + refs_str
        else:
            return summary

    except Exception as e:
        return f"Error: {str(e)}"
    
def raw_json(user_input):
    payload = {"query": user_input}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("answer", {}), data.get("results", [])
        # return data.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

with gr.Blocks() as tabs:
    with gr.Tab("Chat"):
        chatiface = gr.ChatInterface(
            fn=query_api,
            title="Taiwan News Agent"
        )
    with gr.Tab("Raw JSON"):
        iface = gr.Interface(
            fn=raw_json, 
            inputs="text", 
            outputs=[gr.JSON(label="Answer"), gr.JSON(label="Results")], 
        )

tabs.launch(server_name="0.0.0.0", server_port=7860)
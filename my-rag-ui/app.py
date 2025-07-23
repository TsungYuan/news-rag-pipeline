import gradio as gr
import requests

API_URL = "http://semantic-api:8000/rag_agent"

def query_api(user_input, history):
    payload = {"query": user_input}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("results", []), data.get("answer", {})
        # return data.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"
    
iface = gr.Interface(
    fn=query_api, 
    inputs="text", 
    outputs=[gr.JSON(label="Results"), gr.JSON(label="Answer")], 
    title="Semantic Search"
)
iface.launch(server_name="0.0.0.0", server_port=7860)
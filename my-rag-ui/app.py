import gradio as gr
import requests

API_URL = "http://semantic-api:8000/semantic_search"

def query_api(user_input, history):
    payload = {"query": user_input}
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("results", "No answer found.")
        # return data.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"
    
iface = gr.Interface(
    fn=query_api, 
    inputs="text", 
    outputs=gr.JSON(label="Response JSON"), 
    title="Semantic Search"
)
iface.launch(server_name="0.0.0.0", server_port=7860)
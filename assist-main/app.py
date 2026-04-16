import gradio as gr
from agent import Agent

agent = Agent()

def smart_bot(message,history):

    return agent.text_completion(message)

css = '''
.gradio-container { max-width:850px !important; margin:20px auto !important;}
.message { padding: 10px !important; font-size: 14px !important;}
'''

demo = gr.ChatInterface(
    css = css,
    fn = smart_bot,
    title = '智能客服',
    chatbot = gr.Chatbot(height=400, bubble_full_width=False),
    theme = gr.themes.Default(spacing_size='sm', radius_size='sm'),
    textbox=gr.Textbox(placeholder="在此输入您的问题", container=False, scale=7),
    examples = ['你好，你叫什么名字？',  '介绍一下卷积神经网络',  '介绍一下火影忍者的卡卡西'],
    submit_btn = gr.Button('提交', variant='primary'),
    clear_btn = gr.Button('清空记录'),
    retry_btn = None,
    undo_btn = None,
)

if __name__ == '__main__':
    demo.launch(server_name="0.0.0.0", server_port=8000)

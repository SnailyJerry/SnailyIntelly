from openai import OpenAI
import streamlit as st
import time
import random
from PIL import Image

# Initialize OpenAI client
api_keys = [
    "sk-proj-tHIcQ4jl30qvMr4kvhonT3BlbkFJ9lkVdMOrQindHOdUjsJq",
    # You can add more API keys here
]
api_key = random.choice(api_keys)
client = OpenAI(api_key=api_key)

# Define available Assistants
assistants = [
    {
        "name": "贝拉", "id": "asst_SeUjvYOqni9yksDSC3EoqkQf", "alias": "绘本推荐助手", "icon": "👧🏻",
        "description": "我可以为您推荐适合不同年龄段的精彩绘本，激发孩子的阅读兴趣。",
        "guidance": "示例：给我宝宝小名，性别男宝还是女宝，以及出生年月日即可。「 蜗蜗 女宝 20191121 」 我会帮你定制推荐匹配绘本的。"
    },
    {
        "name": "艾米", "id": "asst_IUatrIPuQQcfXW35sKW3wtk2", "alias": "亲子英语助手", "icon": "🙋‍♀️",
        "description": "我可以帮助您设计有趣的英语学习活动，让孩子轻松掌握英语。",
        "guidance": "示例：请设计一个适合7岁孩子的英语单词游戏，主题是动物。"
    },
    {
        "name": "皮特", "id": "asst_8oQvvCwqc5bjeF3GOzEiWQP5", "alias": "皮特猫文案助手", "icon": "🐱",
        "description": "我可以帮您创作有趣的皮特猫精读营的朋友圈文案，写得快又写得好，喵！。",
        "guidance": "示例：请为一本新的皮特猫绘本创作一个吸引人的简短介绍，主题是皮特猫学习游泳。"
    }
]

# Streamlit app configuration
st.set_page_config(
    page_title="蜗牛智能",
    page_icon="🐌",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for styling
st.markdown("""
<style>
    [data-testid="stSidebarContent"] {
        background-color: #FBF7FF !important;
    }
    .stRadio > label {
        background-color: rgba(255, 225, 225, 0.5);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stRadio > label:hover {
        background-color: rgba(255, 225, 225, 0.4);
    }
    .stRadio > label > div:first-child {
        display: none;
    }
    .assistant-icon {
        font-size: 2em;
        margin-right: 10px;
    }
    .assistant-name {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .assistant-description {
        font-size: 0.9em;
        color: #555;
    }
    .guidance-example {
        background-color: rgba(237, 241, 255, 0.7);
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
        font-size: 0.9em;
    }
    .assistant-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .logo-title {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .logo-title h1 {
        font-size: 24px;
        margin: 0;
        margin-left: 10px;
    }
    .sidebar h1 {
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for logo, title, and assistant selection
with st.sidebar:
    # Logo and title
    col1, col2 = st.columns([1, 3])
    with col1:
        try:
            logo = Image.open("./static/logo.png")
            st.image(logo, width=50)
        except FileNotFoundError:
            st.error("Logo file not found. Please check the file path.")
    with col2:
        st.markdown('<h1 class="logo-title">蜗牛智能</h1>', unsafe_allow_html=True)
    
    st.markdown('<h3>选择你的AI助手</h3>', unsafe_allow_html=True)
    
    selected_assistant = st.radio(
        "选择一个助手",
        options=assistants,
        format_func=lambda x: x['name'],
        label_visibility="collapsed"
    )
    
    # Display selected assistant information
    st.markdown(f"""
    <div style="background-color: rgba(255, 225, 225, 0.4); border-radius: 10px; padding: 10px; margin-top: 10px;">
        <span class="assistant-icon">{selected_assistant['icon']}</span>
        <div class="assistant-name">{selected_assistant['name']} ({selected_assistant['alias']})</div>
        <div class="assistant-description">{selected_assistant['description']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display guidance example
    st.markdown(f'<div class="guidance-example"><strong>指导示例：</strong><br>{selected_assistant["guidance"]}</div>', unsafe_allow_html=True)

# Main content area
st.markdown(f'<h1 class="assistant-title">{selected_assistant["icon"]} {selected_assistant["name"]}</h1>', unsafe_allow_html=True)

# User input and file upload
task_input = st.text_area("请参考示例输入：", height=150)
uploaded_files = st.file_uploader("上传图片（可选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
submit_button = st.button("提交生成")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Create an empty placeholder for dynamic updates
response_placeholder = st.empty()

# Status display and feedback
if submit_button and selected_assistant and (task_input or uploaded_files):
    try:
        with st.spinner("正在处理您的请求..."):
            # Prepare message content
            message_content = []
            if task_input:
                message_content.append({
                    "type": "text",
                    "text": task_input
                })
            
            for uploaded_file in uploaded_files:
                # Upload image to OpenAI
                file_response = client.files.create(
                    file=uploaded_file,
                    purpose="assistants"
                )
                
                # Add image to message content
                message_content.append({
                    "type": "image_file",
                    "image_file": {"file_id": file_response.id}
                })

            # Create conversation thread
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": message_content,
                    }
                ]
            )

            # Submit thread and wait for completion
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=selected_assistant['id']
            )

            # Wait for conversation to complete
            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                time.sleep(1)

            # Get conversation messages
            message_response = client.beta.threads.messages.list(thread_id=thread.id)
            messages = message_response.data
            latest_message = messages[0]
            
            # Display result using chat bubble style
            with response_placeholder.container():
                st.chat_message("assistant").write(latest_message.content[0].text.value)

            # Update conversation history
            user_message = f"您：{task_input}"
            if uploaded_files:
                user_message += f" (上传了 {len(uploaded_files)} 张图片)"
            st.session_state.history.append({"role": "user", "content": user_message})
            st.session_state.history.append({"role": "assistant", "name": selected_assistant['name'], "content": latest_message.content[0].text.value})

    except Exception as e:
        st.error(f"发生错误：{e}")
else:
    if submit_button:
        if not selected_assistant:
            st.warning("请先选择一个助手")
        elif not task_input and not uploaded_files:
            st.warning("请输入问题或上传图片")

# Display conversation history
if st.session_state.history:
    st.subheader("对话历史")
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant", avatar=selected_assistant["icon"]):
                    st.write(f"{message['name']}: {message['content']}")

# Use expander to collapse old conversations
with st.expander("查看完整对话历史"):
    for message in st.session_state.history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant", avatar=selected_assistant["icon"]):
                st.write(f"{message['name']}: {message['content']}")

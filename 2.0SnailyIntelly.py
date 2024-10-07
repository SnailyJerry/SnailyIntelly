import streamlit as st
import time
from openai import OpenAI
import random
from PIL import Image
import requests
import json
import base64
from zhipuai import ZhipuAI

# Initialize OpenAI client
# 读取多个 API keys
api_keys = st.secrets["OPENAI_API_KEYS"]
# 随机选择一个 API key
api_key = random.choice(api_keys)
# 使用选中的 API key 初始化 OpenAI 客户端
client = OpenAI(api_key=api_key)

# 智谱AI API keys
zhipuai_api_keys = st.secrets["ZHIPU_API_KEYS"]

# 允许访问的密码列表
valid_passwords = [
    "Snaily!Yes",
    "PeteStory2024",
    "1"
]

# 知识库ID（固定）
knowledge_id = "1842887159632314368"

# Define available Assistants
assistants = [
    {
        "name": "李贝拉", "id": "asst_SeUjvYOqni9yksDSC3EoqkQf", "alias": "绘本推荐助手", "icon": "👧🏻",
        "description": "我可以为您推荐适合不同年龄段的精彩绘本，激发孩子的阅读兴趣。",
        "guidance": "示例：给我宝宝小名，性别男宝还是女宝，以及出生年月日即可。「 蜗蜗 女宝 20191121 」 我会帮你定制推荐匹配绘本的。"
    },
    {
        "name": "张艾米", "id": "asst_IUatrIPuQQcfXW35sKW3wtk2", "alias": "亲子英语助手", "icon": "🙋‍♀️",
        "description": "我可以帮助您设计有趣的英语学习活动，让孩子轻松掌握英语。",
        "guidance": "示例：请设计一个适合7岁孩子的英语单词游戏，主题是动物。"
    },
    {
        "name": "赵皮特", "id": "asst_8oQvvCwqc5bjeF3GOzEiWQP5", "alias": "皮特猫文案助手", "icon": "🐱",
        "description": "我可以帮您创作有趣的皮特猫精读营的朋友圈文案，写得快又写得好，喵！。",
        "guidance": "示例：请为一本新的皮特猫绘本创作一个吸引人的简短介绍，主题是皮特猫学习游泳。"
    },
    {
        "name": "V3.5Mini", "id": "glm-4v-plus", "alias": "截图创作朋友圈助手", "icon": "🤖",
        "description": "我是一个多功能AI助手，可以进行图像分析、知识库检索和管理等任务。",
        "guidance": "示例：上传一张图片并选择一个任务，如描述图片内容或分析人物。"
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

# V3.5Mini functions
def connect_glm4vplus_api(prompts, images):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {random.choice(zhipuai_api_keys)}",
        "Content-Type": "application/json"
    }
    
    images_base64 = []
    for image in images:
        with open(image, "rb") as image_file:
            images_base64.append(base64.b64encode(image_file.read()).decode('utf-8'))
    
    messages = []
    for image_base64 in images_base64:
        for prompt in prompts:
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            })
    
    data = {
        "model": "glm-4v-plus",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 1024,
        "stream": False,
        "tools": [
            {
                "type": "retrieval",
                "retrieval": {
                    "knowledge_id": knowledge_id,
                    "prompt_template": """
                    从文档
                    {{knowledge}}
                    中找到与图片相关的产品信息。
                    """
                }
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        choices = response_data.get("choices", [])
        if not choices:
            return ["没有返回结果"] * len(messages)
        return [choice.get("message", {}).get("content", "没有返回结果") for choice in choices]
    else:
        return [f"请求失败，状态码: {response.status_code}, 信息: {response.text}"] * len(messages)

def retrieve_from_knowledge_base(query):
    client = ZhipuAI(api_key=random.choice(zhipuai_api_keys))
    response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "user", "content": query}
        ],
        tools=[
            {
                "type": "retrieval",
                "retrieval": {
                    "knowledge_id": knowledge_id,
                    "prompt_template": """
                    从文档
                    {{knowledge}}
                    中找到问题
                    {{question}}
                    的答案。找到后直接给出答案，如果找不到则使用模型自身知识，并告知信息不来自文档。
                    """
                }
            }
        ],
        stream=True
    )
    return response

def modify_knowledge_base(name, description):
    client = ZhipuAI(api_key=random.choice(zhipuai_api_keys))
    result = client.knowledge.modify(
        knowledge_id=knowledge_id,
        embedding_id=3,
        name=name,
        description=description
    )
    return result

def query_knowledge_base(page=1, size=10):
    client = ZhipuAI(api_key=random.choice(zhipuai_api_keys))
    result = client.knowledge.query(
        page=page,
        size=size
    )
    return result

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

# Password verification for V3.5Mini
if selected_assistant["name"] == "V3.5Mini":
    password = st.text_input("请输入内部密码：", type="password")
    if password not in valid_passwords:
        st.warning("🔒 输入有效密码以访问V3.5Mini AI应用。")
        st.stop()

# V3.5Mini specific UI
if selected_assistant["name"] == "V3.5Mini":
    function_choice = st.radio("选择功能", ["图像分析", "知识库检索", "知识库管理"])

    if function_choice == "图像分析":
        st.subheader("上传图片")
        uploaded_files = st.file_uploader("请选择要上传的图片(最多5张,单张效果最好)：", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="fileUploader", help="最多可以上传 5 张图片。")

        if uploaded_files and len(uploaded_files) > 5:
            st.warning("⚠️ 最多只能上传 5 张图片，请重新选择。")
            uploaded_files = uploaded_files[:5]

        st.subheader("选择任务")
        selected_task = st.radio("请选择一个任务：", [
            "🖼️ Task 1: 描述图片",
            "👥 Task 2: 描述图片人物",
            "🔍 Task 3: 描述视角",
            "🔤 Task 4: 描述文字"
        ])

        prompts = {
            "🖼️ Task 1: 描述图片": "请仔细分析我上传的图片（包括聊天截图，学员留言，评价，反馈，成长时刻等），提取关键信息和情感元素。然后，请创作一篇约300字的文案内容，要求如下：...",
            "👥 Task 2: 描述图片人物": "请仔细分析图片中的人物及场景，并结合知识库中的产品信息，创作一篇约200字的描述：...",
            "🔍 Task 3: 描述视角": "请描述这张图片的拍摄视角和角度，包括相机的位置、拍摄高度和焦距等信息，以及它们对整体画面的影响。",
            "🔤 Task 4: 描述文字": "请描述图片中的文字内容，包括所有可见的标志、说明、广告牌等内容，并解释它们的可能意义。"
        }

        selected_prompts = [prompts[selected_task]]

        if st.button("🚀 开始创作"):
            if not uploaded_files or not selected_prompts:
                st.warning("⚠️ 请上传图片并选择一个任务！")
            else:
                with st.spinner("处理中，请稍候..."):
                    temp_image_paths = []
                    for i, uploaded_file in enumerate(uploaded_files):
                        temp_image_path = f"temp_image_{i}.png"
                        with open(temp_image_path, "wb") as f:
                            f.write(uploaded_file.read())
                        temp_image_paths.append(temp_image_path)
                    
                    results = connect_glm4vplus_api(selected_prompts, temp_image_paths)
                    
                    result_index = 0
                    total_results = len(uploaded_files) * len(selected_prompts)
                    for i, uploaded_file in enumerate(uploaded_files):
                        if result_index < len(results):
                            st.subheader("生成结果")
                            st.text_area("", value=results[result_index], height=300, key=f"results_text_{i}")
                            result_index += 1

    elif function_choice == "知识库检索":
        st.subheader("知识库检索")
        query = st.text_input("请输入您的问题：")
        if st.button("🔍 搜索"):
            if query:
                with st.spinner("正在检索知识库..."):
                    response = retrieve_from_knowledge_base(query)
                    st.subheader("检索结果")
                    full_response = ""
                    response_container = st.empty()
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_response += content
                            response_container.text_area("", value=full_response, height=300)
            else:
                st.warning("请输入问题后再搜索。")

    elif function_choice == "知识库管理":
        st.subheader("知识库管理")
        
        st.subheader("修改知识库")
        new_name = st.text_input("新的知识库名称（可选）：")
        new_description = st.text_area("新的知识库描述（可选）：")
        if st.button("修改知识库"):
            if new_name or new_description:
                result = modify_knowledge_base(new_name, new_description)
                st.json(result)
            else:
                st.warning("请至少输入新的名称或描述。")
        
        st.subheader("查询知识库")
        page = st.number_input("页码", min_value=1, value=1)
        size = st.number_input("每页数量", min_value=1, max_value=100, value=10)
        if st.button("查询知识库"):
            result = query_knowledge_base(page, size)
            st.json(result)

else:
    # User input and file upload for other assistants
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

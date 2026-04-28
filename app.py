import streamlit as st
import pandas as pd
import json
import google.generativeai as genai  # 1. 把 import 移到最上方

# --- 页面基础配置 ---
st.set_page_config(page_title="多语种日语学习助手", layout="wide")

st.title("🏮 个人专用日语学习 App")
st.caption("基于中、韩、西三语背景开发")

# --- AI 配置 (放在逻辑块外面) ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.sidebar.warning("⚠️ 请在 Streamlit Secrets 中配置 GEMINI_API_KEY")

# --- 侧边栏：组合与级别设定 ---
st.sidebar.header("🛠️ 学习设定")

combo_option = st.sidebar.selectbox(
    "选择学习组合",
    ["CH-JP", "KO-JP", "JP-SP", "CH-KO", "JP-CH", "KO-CH", "SP-JP"]
)

level = st.sidebar.radio(
    "学习阶段",
    ["基础：发音与字母", "进阶：全信息交叉搜索", "挑战：AI 语法分析"]
)

# --- 加载数据函数 ---
@st.cache_data
def load_data(combo):
    file_path = f"{combo}.parquet"
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        st.error(f"无法读取文件 {file_path}: {e}")
        return None

df = load_data(combo_option)

# --- 模块 1：基础发音 ---
if level == "基础：发音与字母":
    st.header("🅰️ 五十音图 x 西班牙语辅助")
    st.info("💡 提示：日语的 a, i, u, e, o 与西班牙语发音几乎完全一致！")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("五元音")
        st.code("あ (a) - Como 'Amigo'\nい (i) - Como 'Isla'\nう (u) - Como 'Uva'\nえ (e) - Como 'Elefante'\nお (o) - Como 'Hola'")
    with col2:
        st.subheader("学习建议")
        st.write("你会韩语，日语的收音（P/T/K）和韩语的终声（Batchim）逻辑很像，可以互相参考。")

# --- 模块 2：全信息交叉搜索 ---
elif level == "进阶：全信息交叉搜索":
    st.header(f"🔍 交叉搜索核心 - {combo_option}")
    
    if df is not None:
        search_query = st.text_input("输入关键词（支持日文、中文、韩文或西文）：")
        
        if search_query:
            mask = (
                df['word'].str.contains(search_query, na=False, case=False) |
                df['senses'].str.contains(search_query, na=False, case=False) |
                df['categories'].str.contains(search_query, na=False, case=False)
            )
            
            if 'etymology_texts' in df.columns:
                mask |= df['etymology_texts'].str.contains(search_query, na=False, case=False)
            
            results = df[mask]
            st.write(f"找到 {len(results)} 条相关结果：")
            
            for _, row in results.head(20).iterrows():
                with st.expander(f"📌 {row['word']} ({row.get('pos_title', '未知词性')})"):
                    st.write(f"**释义：** {row['senses']}")
                    if 'sounds' in row and row['sounds']:
                        st.write(f"**读音/音频：** {row['sounds']}")
                    if 'etymology_texts' in row and row['etymology_texts']:
                        st.info(f"🧬 **词源（Etymology）：**\n{row['etymology_texts']}")
                    if 'categories' in row and row['categories']:
                        st.warning(f"🏷️ **分类标签：**\n{row['categories']}")

# --- 模块 3：AI 语法练习 ---
elif level == "挑战：AI 语法分析":
    st.header("🤖 Gemini AI 导师")
    st.write("输入日语句子，AI 会结合你的中、韩、西语背景进行深度分析。")
    
    user_input = st.text_area("输入你想分析的日语或对比句子：", placeholder="例如：勉強すればするほど、難しくなります。")
    
    if st.button("开始 AI 深度分析"):
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("请先在 Secrets 中设置 API Key！")
        elif user_input:
            with st.spinner("AI 老师正在思考中..."):
                try:
                    prompt = f"""
                    你是一位精通日语、中文、韩语和西班牙语的语言学专家。
                    用户目前的水平是：中文母语、韩语熟练、西班牙语B1、日语初学者。
                    请分析以下日语句子：'{user_input}'
                    
                    要求：
                    1. 给出中文翻译。
                    2. 寻找该句子与韩语在语法上的相似之处（例如助词对应、语序）。
                    3. 如果发音上有与西班牙语相似的部分，请指出。
                    4. 解释重点词汇和语法点。
                    """
                    response = model.generate_content(prompt)
                    st.markdown("### 📝 AI 分析结果")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"AI 调用出错: {e}")
        else:
            st.warning("请输入内容后再点击分析。")

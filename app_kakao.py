import streamlit as st
import pandas as pd
import os
import platform
from collections import Counter
from konlpy.tag import Okt
import google.generativeai as genai
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 폰트 설정 (배포 환경 대응)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="카카오톡 대화 분석기 (Ultimate)",
    page_icon="🎁",
    layout="wide"
)

# 폰트 설정 우회 로직
def get_font_path():
    paths = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf', # Linux (Streamlit Cloud)
        '/System/Library/Fonts/AppleGothic.ttf',          # Mac
        'C:/Windows/Fonts/malgun.ttf'                     # Windows
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None # 폰트가 없을 경우 None 반환 (WordCloud 기본폰트 사용)

FONT_PATH = get_font_path()

# Secrets에서 API 키 가져오기
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = None
    st.sidebar.warning("⚠️ Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다.")

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
@st.cache_resource
def get_tokenizer():
    return Okt()

@st.cache_data
def load_data(uploaded_files):
    all_data = []
    for uploaded_file in uploaded_files:
        try:
            # 헤더 탐색 및 로드 (기존 로직 유지)
            content = uploaded_file.read()
            for enc in ['utf-8', 'cp949', 'utf-16']:
                try:
                    decoded = content.decode(enc)
                    df_temp = pd.read_csv(BytesIO(content), encoding=enc, header=None)
                    break
                except: continue
            
            header_row_idx = 0
            for idx, row in df_temp.iterrows():
                if 'Date' in str(row.values) and 'User' in str(row.values):
                    header_row_idx = idx
                    break
            
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, header=header_row_idx, encoding=enc)
            df.columns = [str(c).strip() for c in df.columns]
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
                df['Year'] = df['Date'].dt.year
                all_data.append(df)
        except Exception as e:
            st.error(f"파일 로드 오류: {e}")
            
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

@st.cache_data
def extract_nouns(text_data, top_n=50):
    okt = get_tokenizer()
    nouns = []
    sample_text = text_data[:10000] if len(text_data) > 10000 else text_data
    for text in sample_text:
        if isinstance(text, str):
            nouns.extend([n for n in okt.nouns(text) if len(n) > 1])
    return Counter(nouns).most_common(top_n)

# -----------------------------------------------------------------------------
# 3. UI 컴포넌트 (PNG 다운로드 추가)
# -----------------------------------------------------------------------------
def get_time_of_day_label(hour):
    if 5 <= hour < 12: return "🌞 아침형 인간"
    elif 12 <= hour < 18: return "☕ 오후의 수다쟁이"
    elif 18 <= hour < 24: return "🌙 저녁형 인간"
    else: return "🦉 올빼미족"

def show_wrapped_ui(df, year):
    # CSS 유지 (생략, 원본 코드와 동일)
    st.markdown(f"## 🎉 {year}년 우리들의 기록 (Wrapped)")
    
    total_msgs = len(df)
    daily_counts = df['Date'].dt.date.value_counts()
    best_day_str = daily_counts.idxmax().strftime("%m월 %d일") if not daily_counts.empty else "-"
    
    # ... (기존 통계 계산 로직 동일) ...
    
    # AI 분석 (Secrets의 API_KEY 사용)
    if API_KEY and st.button("✨ AI 주제 분석"):
        with st.spinner("분석 중..."):
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash') # 최신 모델명 확인 필요
            sample = df['Message'].dropna().sample(min(100, len(df))).tolist()
            response = model.generate_content(f"다음 카톡 주제 5가지를 콤마로 구분: {sample}")
            st.write(response.text)

def show_ai_report_ui(df, year):
    st.subheader(f"🤖 Gemini 심층 리포트")
    if not API_KEY:
        st.warning("API Key가 설정되지 않았습니다.")
        return
    
    if st.button("📑 리포트 생성"):
        with st.spinner("작성 중..."):
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash')
            sample = df['Message'].dropna().sample(min(150, len(df))).tolist()
            prompt = f"다음 대화를 분석해 분위기, 주제, 총평을 마크다운으로 작성: {sample}"
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.download_button("📥 리포트(.txt) 다운로드", response.text, file_name=f"report_{year}.txt")

# -----------------------------------------------------------------------------
# 4. 메인 로직
# -----------------------------------------------------------------------------
uploaded_files = st.sidebar.file_uploader("카카오톡 CSV 업로드", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    df = load_data(uploaded_files)
    if not df.empty:
        all_years = sorted(df['Year'].dropna().astype(int).unique())
        selected_year = st.sidebar.selectbox("연도 선택", all_years, index=len(all_years)-1)
        year_df = df[df['Year'] == selected_year]
        
        tabs = st.tabs(["🎁 Wrapped", "🎭 성격 분석", "🤖 심층 리포트", "📊 발화량", "☁️ 키워드"])
        
        with tabs[0]: show_wrapped_ui(year_df, selected_year)
        
        with tabs[2]: show_ai_report_ui(year_df, selected_year)
        
        with tabs[4]: # 키워드 & PNG 다운로드
            st.subheader("주요 키워드 워드클라우드")
            if st.button("분석 시작"):
                nouns = extract_nouns(year_df['Message'].dropna().tolist())
                if nouns:
                    wc = WordCloud(font_path=FONT_PATH, background_color="white", width=800, height=400).generate_from_frequencies(dict(nouns))
                    
                    # 이미지 표시
                    fig, ax = plt.subplots()
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    st.pyplot(fig)
                    
                    # PNG 다운로드 로직
                    buf = BytesIO()
                    plt.savefig(buf, format="png")
                    st.download_button(
                        label="📥 워드클라우드 PNG 다운로드",
                        data=buf.getvalue(),
                        file_name=f"wordcloud_{selected_year}.png",
                        mime="image/png"
                    )
                else:
                    st.warning("추출된 명사가 없습니다.")

else:
    st.info("👈 사이드바에서 카카오톡 CSV 파일을 업로드해주세요.")

import streamlit as st
import pandas as pd
import os
import platform
from collections import Counter
from konlpy.tag import Okt
import google.generativeai as genai
import plotly.express as px
import matplotlib.pyplot as plt
import json
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 API 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="카카오톡 대화 분석기 (Ultimate Edition)",
    page_icon="🎁",
    layout="wide"
)

# Secrets에서 API 키 로드 (배포 환경)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    API_KEY = None

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 함수
# -----------------------------------------------------------------------------
@st.cache_resource
def get_tokenizer():
    return Okt()

@st.cache_data
def load_data(uploaded_files):
    all_data = []
    for uploaded_file in uploaded_files:
        try:
            content = uploaded_file.read()
            # 인코딩 자동 감지
            detected_df = None
            for enc in ['utf-8', 'cp949', 'utf-16']:
                try:
                    uploaded_file.seek(0)
                    temp_df = pd.read_csv(uploaded_file, header=None, encoding=enc)
                    used_encoding = enc
                    detected_df = temp_df
                    break
                except: continue
            
            if detected_df is None: continue

            # 헤더 위치 찾기
            header_row_idx = 0
            for idx, row in detected_df.iterrows():
                row_values = [str(val).strip() for val in row.values]
                if 'Date' in row_values and 'User' in row_values:
                    header_row_idx = idx
                    break
            
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, header=header_row_idx, encoding=used_encoding)
            df.columns = [str(c).strip() for c in df.columns]
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
                df['Year'] = df['Date'].dt.year
                all_data.append(df)
        except Exception as e:
            st.error(f"파일 로드 중 오류: {e}")
            
    if all_data: return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

@st.cache_data
def extract_nouns(text_data, top_n=50):
    okt = get_tokenizer()
    nouns = []
    # 에러 방지를 위해 실제 데이터 길이 확인 후 샘플링
    sample_size = min(len(text_data), 10000)
    for text in text_data[:sample_size]:
        if isinstance(text, str):
            nouns.extend([n for n in okt.nouns(text) if len(n) > 1])
    return Counter(nouns).most_common(top_n)

# -----------------------------------------------------------------------------
# 3. UI 컴포넌트 함수들 (기존 로직 유지)
# -----------------------------------------------------------------------------
def get_time_of_day_label(hour):
    if 5 <= hour < 12: return "🌞 아침형 인간"
    elif 12 <= hour < 18: return "☕ 오후의 수다쟁이"
    elif 18 <= hour < 24: return "🌙 저녁형 인간"
    else: return "🦉 올빼미족"

def show_wrapped_ui(df, year):
    st.markdown("""
    <style>
    .wrapped-card { padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white; height: 100%; }
    .wrapped-title { font-size: 1.0rem; opacity: 0.9; margin-bottom: 5px; }
    .wrapped-value { font-size: 2.0rem; font-weight: bold; margin-bottom: 5px; }
    .wrapped-desc { font-size: 0.8rem; opacity: 0.9; }
    .card-dark { background: linear-gradient(135deg, #434343 0%, #000000 100%); }
    .card-blue { background: linear-gradient(120deg, #2980b9 0%, #6dd5fa 100%); }
    .card-pink { background: linear-gradient(120deg, #f093fb 0%, #f5576c 100%); }
    .card-green { background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%); color: #333 !important; }
    .card-gold { background: linear-gradient(120deg, #f6d365 0%, #fda085 100%); color: #333 !important; }
    .ai-tag { display: inline-block; background-color: #f0f2f6; color: #31333F; padding: 5px 15px; border-radius: 20px; margin: 5px; font-weight: bold; border: 1px solid #d0d0d0; }
    </style>
    """, unsafe_allow_html=True)

    total_msgs = len(df)
    daily_counts = df['Date'].dt.date.value_counts()
    best_day_str, best_day_count = ("-", 0)
    if not daily_counts.empty:
        best_day = daily_counts.idxmax()
        best_day_count = daily_counts.max()
        best_day_str = best_day.strftime("%m월 %d일")

    hourly_counts = df['Date'].dt.hour.value_counts()
    best_hour = hourly_counts.idxmax() if not hourly_counts.empty else 0
    time_label = get_time_of_day_label(best_hour)

    user_counts = df['User'].value_counts()
    mvp_user = user_counts.idxmax() if not user_counts.empty else "-"
    mvp_ratio = int((user_counts.max() / total_msgs) * 100) if total_msgs > 0 else 0

    all_msgs = df['Message'].dropna().tolist()
    top_nouns = extract_nouns(all_msgs, top_n=1)
    top_word, top_word_count = top_nouns[0] if top_nouns else ("데이터 부족", 0)

    st.markdown(f"## 🎉 {year}년 우리들의 기록 (Wrapped)")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="wrapped-card card-dark"><div class="wrapped-title">총 대화</div><div class="wrapped-value">{total_msgs:,}</div><div class="wrapped-desc">우리의 히스토리</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="wrapped-card card-green"><div class="wrapped-title" style="color:#333">올해의 MVP</div><div class="wrapped-value" style="color:#333">{mvp_user}</div><div class="wrapped-desc" style="color:#333">지분율 {mvp_ratio}%</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="wrapped-card card-gold"><div class="wrapped-title" style="color:#333">올해의 단어</div><div class="wrapped-value" style="color:#333">"{top_word}"</div><div class="wrapped-desc" style="color:#333">{top_word_count}회 언급</div></div>""", unsafe_allow_html=True)
    
    c4, c5 = st.columns(2)
    with c4: st.markdown(f"""<div class="wrapped-card card-blue"><div class="wrapped-title">황금 시간대</div><div class="wrapped-value">{best_hour}시</div><div class="wrapped-desc">{time_label}</div></div>""", unsafe_allow_html=True)
    with c5: st.markdown(f"""<div class="wrapped-card card-pink"><div class="wrapped-title">최고의 날</div><div class="wrapped-value">{best_day_str}</div><div class="wrapped-desc">하루 {best_day_count}톡</div></div>""", unsafe_allow_html=True)

    if API_KEY:
        st.markdown("### 🤖 AI 키워드 요약")
        if st.button("✨ 주제 분석 보기"):
            with st.spinner("분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    sample = df['Message'].dropna().sample(min(150, len(df))).tolist()
                    prompt = f"다음 대화에서 핵심 주제 5가지를 뽑아 '주제1, 주제2' 형태로만 답변해줘: {sample}"
                    response = model.generate_content(prompt)
                    topics = response.text.split(",")
                    tags_html = "".join([f"<span class='ai-tag'># {t.strip()}</span>" for t in topics if t.strip()])
                    st.markdown(f"<div style='text-align: center; margin: 10px 0;'>{tags_html}</div>", unsafe_allow_html=True)
                except Exception as e: st.error(f"분석 실패: {e}")

def show_personality_analysis(df):
    st.subheader("🎭 AI가 본 '부캐' 프로필")
    if not API_KEY:
        st.warning("Gemini API Key가 설정되지 않았습니다.")
        return

    selected_users = st.multiselect("분석할 멤버 선택", df['User'].unique(), default=df['User'].value_counts().head(3).index.tolist())

    if st.button("🕵️ 프로필 분석 시작"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        cols = st.columns(2)
        for idx, user in enumerate(selected_users):
            with cols[idx % 2]:
                with st.spinner(f"'{user}' 분석 중..."):
                    user_series = df[df['User'] == user]['Message'].dropna()
                    user_msgs = user_series.sample(min(100, len(user_series))).tolist()
                    prompt = f"다음 대화를 바탕으로 {user}의 재미있는 RPG 프로필을 JSON(title, mbti, animal, keywords, skill, desc)으로 작성: {user_msgs}"
                    try:
                        response = model.generate_content(prompt)
                        data = json.loads(response.text.replace("```json", "").replace("```", ""))
                        st.markdown(f"""
                        <div style="background:#fff; border:1px solid #ddd; padding:20px; border-radius:15px; margin-bottom:10px;">
                            <h3>{data['animal']} {user}</h3>
                            <p><b>칭호:</b> {data['title']} | <b>MBTI:</b> {data['mbti']}</p>
                            <p><b>보유스킬:</b> {data['skill']}</p>
                            <p>{data['desc']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except: st.error(f"{user} 분석 실패")

def show_ai_report_ui(df, year):
    st.subheader(f"🤖 {year}년 심층 리포트")
    if not API_KEY:
        st.warning("Gemini API Key가 필요합니다.")
        return
    if st.button("📑 리포트 생성"):
        with st.spinner("AI 분석 중..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            sample = df['Message'].dropna().sample(min(200, len(df))).tolist()
            prompt = f"다음 카톡 대화 샘플을 분석해서 분위기, 주요 관심사, 한 줄 총평을 마크다운으로 작성해줘: {sample}"
            response = model.generate_content(prompt)
            st.markdown(response.text)

# -----------------------------------------------------------------------------
# 4. 메인 앱 로직
# -----------------------------------------------------------------------------
st.title("💬 카카오톡 연도별 대화 분석기")

# [수정사항 4] 파일 업로드 가이드 추가
with st.expander("📂 시작하기 전, 데이터 추출 방법 확인", expanded=True):
    st.markdown("""
    1. 분석하고 싶은 **카카오톡 채팅방**에 접속합니다.
    2. 오른쪽 상단 **메뉴(≡)** 아이콘을 클릭합니다.
    3. 하단 **설정(톱니바퀴)** 아이콘을 클릭합니다.
    4. **대화 내용 관리** > **대화 내용 저장**을 클릭합니다.
    5. 저장된 **텍스트 파일(.txt) 또는 CSV**를 아래에 업로드하세요.
    """)

uploaded_files = st.sidebar.file_uploader("카카오톡 파일 업로드", type=['csv', 'txt'], accept_multiple_files=True)

if uploaded_files:
    df = load_data(uploaded_files)
    if not df.empty:
        all_years = sorted(df['Year'].dropna().astype(int).unique())
        selected_year = st.sidebar.selectbox("분석할 연도 선택", all_years, index=len(all_years)-1)
        year_df = df[df['Year'] == selected_year]
        
        tabs = st.tabs(["🎁 Wrapped", "🎭 성격 분석", "🤖 심층 리포트", "📊 발화량", "📋 데이터"])
        
        with tabs[0]: show_wrapped_ui(year_df, selected_year)
        with tabs[1]: show_personality_analysis(year_df)
        with tabs[2]: show_ai_report_ui(year_df, selected_year)
        with tabs[3]:
            st.subheader("사용자별 통계")
            uc = year_df['User'].value_counts().reset_index()
            uc.columns = ['User', 'Count']
            st.plotly_chart(px.bar(uc, x='User', y='Count', color='User', text_auto=True), use_container_width=True)
        with tabs[4]: st.dataframe(year_df)
    else:
        st.warning("데이터를 읽을 수 없습니다. 파일 형식을 확인해주세요.")
else:
    st.info("👈 사이드바에서 파일을 업로드하면 분석이 시작됩니다.")

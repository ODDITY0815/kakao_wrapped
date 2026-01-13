import streamlit as st
import pandas as pd
import os
import platform
from collections import Counter
from konlpy.tag import Okt
import google.generativeai as genai
import plotly.express as px
import json

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="카카오톡 대화 분석기 (PC)",
    page_icon="🎁",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 함수
# -----------------------------------------------------------------------------
@st.cache_resource
def get_tokenizer():
    return Okt()

@st.cache_data
def load_data(uploaded_files):
    """CSV 파일의 헤더 위치를 자동으로 찾아서 로드하는 함수"""
    all_data = []
    for uploaded_file in uploaded_files:
        try:
            # 1. 헤더 탐색
            try:
                temp_df = pd.read_csv(uploaded_file, header=None)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                temp_df = pd.read_csv(uploaded_file, header=None, encoding='cp949')

            header_row_idx = None
            for idx, row in temp_df.iterrows():
                row_values = [str(val).strip() for val in row.values]
                if 'Date' in row_values and 'User' in row_values:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None: header_row_idx = 0 

            # 2. 데이터 로드
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, header=header_row_idx)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, header=header_row_idx, encoding='cp949')

            # 3. 전처리
            df.columns = [str(c).strip() for c in df.columns]
            if 'Date' not in df.columns: continue

            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            df['Year'] = df['Date'].dt.year
            
            all_data.append(df)
            
        except Exception as e:
            st.error(f"파일 로드 중 오류 ({uploaded_file.name}): {e}")
            
    if all_data: return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

@st.cache_data
def extract_nouns(text_data, top_n=50):
    """명사 추출 함수"""
    okt = get_tokenizer()
    nouns = []
    if len(text_data) > 10000: text_data = text_data[:10000] # 샘플링

    for text in text_data:
        if isinstance(text, str):
            nouns.extend([n for n in okt.nouns(text) if len(n) > 1])
    return Counter(nouns).most_common(top_n)

# -----------------------------------------------------------------------------
# 3. UI 컴포넌트 함수들
# -----------------------------------------------------------------------------
def get_time_of_day_label(hour):
    if 5 <= hour < 12: return "🌞 아침형 인간"
    elif 12 <= hour < 18: return "☕ 오후의 수다쟁이"
    elif 18 <= hour < 24: return "🌙 저녁형 인간"
    else: return "🦉 올빼미족"

def show_wrapped_ui(df, year, api_key=None):
    """[Tab 1] Wrapped (연말결산) UI"""
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

    # 데이터 계산
    total_msgs = len(df)
    daily_counts = df['Date'].dt.date.value_counts()
    best_day_str, best_day_count = ("-", 0)
    if not daily_counts.empty:
        best_day = daily_counts.idxmax()
        best_day_count = daily_counts.max()
        best_day_str = best_day.strftime("%m월 %d일")

    hourly_counts = df['Date'].dt.hour.value_counts()
    best_hour, time_label = (0, "-")
    if not hourly_counts.empty:
        best_hour = hourly_counts.idxmax()
        time_label = get_time_of_day_label(best_hour)

    user_counts = df['User'].value_counts()
    mvp_user, mvp_ratio = ("-", 0)
    if not user_counts.empty:
        mvp_user = user_counts.idxmax()
        mvp_ratio = int((user_counts.max() / total_msgs) * 100) if total_msgs > 0 else 0

    all_msgs = df['Message'].dropna().tolist()
    top_nouns = extract_nouns(all_msgs, top_n=1)
    top_word, top_word_count = top_nouns[0] if top_nouns else ("데이터 부족", 0)

    # UI 렌더링
    st.markdown(f"## 🎉 {year}년 우리들의 기록 (Wrapped)")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="wrapped-card card-dark"><div class="wrapped-title">총 대화</div><div class="wrapped-value">{total_msgs:,}</div><div class="wrapped-desc">우리의 히스토리</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="wrapped-card card-green"><div class="wrapped-title" style="color:#333">올해의 MVP</div><div class="wrapped-value" style="color:#333">{mvp_user}</div><div class="wrapped-desc" style="color:#333">지분율 {mvp_ratio}%</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="wrapped-card card-gold"><div class="wrapped-title" style="color:#333">올해의 단어</div><div class="wrapped-value" style="color:#333">"{top_word}"</div><div class="wrapped-desc" style="color:#333">{top_word_count}회 언급</div></div>""", unsafe_allow_html=True)
    
    c4, c5 = st.columns(2)
    with c4: st.markdown(f"""<div class="wrapped-card card-blue"><div class="wrapped-title">황금 시간대</div><div class="wrapped-value">{best_hour}시</div><div class="wrapped-desc">{time_label}</div></div>""", unsafe_allow_html=True)
    with c5: st.markdown(f"""<div class="wrapped-card card-pink"><div class="wrapped-title">최고의 날</div><div class="wrapped-value">{best_day_str}</div><div class="wrapped-desc">하루 {best_day_count}톡</div></div>""", unsafe_allow_html=True)

    # AI 요약
    st.markdown("### 🤖 AI 키워드 요약")
    if api_key and st.button("✨ 주제 분석 보기"):
        with st.spinner("Gemini 2.0 분석 중..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                sample_size = min(150, len(df))
                sample = df['Message'].dropna().sample(sample_size).tolist() if sample_size > 0 else []
                prompt = f"다음 카톡 대화({year}년)에서 핵심 주제 5가지를 뽑아 '주제1, 주제2' 형태로 콤마로만 구분해줘: {sample}"
                response = model.generate_content(prompt)
                topics = response.text.replace("\n", "").split(",")
                
                tags_html = ""
                for t in topics:
                    clean_t = t.strip().replace("'", "").replace('"', "")
                    if clean_t:
                        tags_html += f"<span class='ai-tag'># {clean_t}</span>"

                st.markdown(f"<div style='text-align: center; margin: 10px 0;'>{tags_html}</div>", unsafe_allow_html=True)
            except Exception as e: st.error(f"오류: {e}")

def show_personality_analysis(df, api_key):
    """[Tab 2] 사용자별 성격 분석 UI (RPG 스타일)"""
    st.subheader("🎭 AI가 본 '부캐' 프로필")
    st.info("💡 대화 내용을 바탕으로 MBTI, 숨겨진 특수 능력, 그리고 한 줄 평을 분석합니다.")
    
    if not api_key:
        st.warning("Gemini API Key가 설정되지 않았습니다. Streamlit Secrets에 API Key를 추가해주세요.")
        return

    top_users = df['User'].value_counts().head(3).index.tolist()
    all_users = df['User'].unique().tolist()
    selected_users = st.multiselect("분석할 멤버 선택 (최대 4명 권장)", all_users, default=top_users)

    if st.button("🕵️ 프로필 분석 시작"):
        if not selected_users:
            st.warning("멤버를 선택해주세요.")
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # CSS
        st.markdown("""
        <style>
        .persona-card { background-color: #ffffff; border: 2px solid #f0f0f0; border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); position: relative; overflow: hidden; }
        .persona-animal { font-size: 3.5rem; position: absolute; top: 15px; right: 20px; opacity: 0.8; }
        .persona-name { font-size: 1.5rem; font-weight: 800; color: #333; margin-bottom: 5px; }
        .persona-title { font-size: 1.1rem; color: #555; font-weight: bold; background: linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%); display: inline-block; padding: 2px 10px; border-radius: 8px; margin-bottom: 10px; }
        .persona-mbti { font-size: 0.9rem; color: #888; margin-bottom: 15px; font-style: italic; }
        .persona-tag { display: inline-block; background: #f1f3f5; color: #495057; padding: 4px 10px; border-radius: 15px; font-size: 0.85rem; font-weight: 600; margin-right: 5px; margin-bottom: 5px; }
        .persona-skill { margin-top: 15px; padding: 10px; background-color: #fff3cd; border-radius: 8px; font-size: 0.95rem; color: #856404; font-weight: bold; }
        .persona-desc { margin-top: 15px; font-size: 0.95rem; line-height: 1.6; color: #444; border-top: 1px solid #eee; padding-top: 10px; }
        </style>
        """, unsafe_allow_html=True)

        progress_bar = st.progress(0)
        cols = st.columns(2)
        
        for idx, user in enumerate(selected_users):
            col = cols[idx % 2]
            with col:
                with st.spinner(f"'{user}'님의 영혼을 들여다보는 중..."):
                    user_df = df[df['User'] == user]['Message'].dropna()
                    if len(user_df) == 0:
                        st.warning(f"{user}님의 메시지가 없습니다.")
                        continue
                    
                    # 샘플 크기를 실제 데이터 크기와 비교
                    sample_size = min(120, len(user_df))
                    user_msgs = user_df.sample(sample_size).tolist()

                    prompt = f"""
                    당신은 '예리하고 유머러스한 심리 분석가'입니다. 다음은 '{user}' 님의 대화입니다: {user_msgs}
                    친구들이 보고 '빵 터질 수 있는' 재미있는 프로필을 만들어주세요. JSON 포맷만 출력하세요:
                    {{
                        "title": "웃긴 RPG 칭호 (예: 팩트살인마)",
                        "mbti": "예상 MBTI와 짧은 이유",
                        "animal": "동물 이모지 1개",
                        "keywords": ["태그1", "태그2"],
                        "skill": "종특/특수능력 (예: 읽씹하기)",
                        "desc": "3문장 요약 설명"
                    }}
                    """
                    try:
                        response = model.generate_content(prompt)
                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)
                        
                        tags_html = "".join([f"<span class='persona-tag'>#{k}</span>" for k in data.get('keywords', [])])
                        
                        st.markdown(f"""
                        <div class="persona-card">
                            <span class="persona-animal">{data.get('animal', '👤')}</span>
                            <div class="persona-name">{user}</div>
                            <div class="persona-title">{data.get('title', '알 수 없음')}</div>
                            <div class="persona-mbti">🧠 {data.get('mbti', '분석 불가')}</div>
                            <div>{tags_html}</div>
                            <div class="persona-skill">⚡ 보유 스킬: {data.get('skill', '능력 없음')}</div>
                            <div class="persona-desc">{data.get('desc', '설명이 없습니다.')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"{user}: 분석 실패 - {str(e)}")
            progress_bar.progress((idx + 1) / len(selected_users))
        progress_bar.empty()

def show_ai_report_ui(df, year, api_key):
    """[Tab 3] AI 심층 리포트"""
    st.subheader(f"🤖 Gemini가 분석한 {year}년 심층 리포트")
    st.info("💡 대화 전체 흐름을 파악하여 분위기, 관심사, 총평을 요약합니다.")
    
    if not api_key:
        st.warning("Gemini API Key가 설정되지 않았습니다. Streamlit Secrets에 API Key를 추가해주세요.")
    else:
        if st.button("📑 심층 리포트 생성하기"):
            with st.spinner("AI가 대화 내용을 정밀 분석 중입니다..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # 샘플링 (토큰 제한 고려)
                    sample_size = min(200, len(df))
                    sample_messages = df['Message'].dropna().sample(sample_size).tolist() if sample_size > 0 else []
                    
                    prompt = f"""
                    당신은 전문 데이터 분석가입니다. 다음은 {year}년도의 카카오톡 대화방 샘플 데이터입니다.
                    
                    대화 샘플: {sample_messages}
                    
                    위 내용을 바탕으로 다음 3가지를 분석해서 마크다운 형식으로 깔끔하게 보고서를 작성해주세요:
                    
                    1. 🗣️ **전반적인 대화의 분위기**
                       - 대화가 주로 어떤 톤인지 (유머러스, 진지함, 정보공유, 잡담 등)
                    
                    2. 🔥 **주요 관심사나 주제**
                       - 이들이 가장 많이 이야기한 토픽 3~4가지를 구체적으로 설명
                    
                    3. 📝 **한 줄 총평**
                       - 이 해의 대화를 아우르는 멋진 한 줄 요약
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"API 호출 중 에러 발생: {e}")

# -----------------------------------------------------------------------------
# 4. 메인 앱 로직
# -----------------------------------------------------------------------------

# Streamlit Secrets에서 API Key 가져오기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = None
    st.warning("⚠️ Streamlit Secrets에 GEMINI_API_KEY가 설정되지 않았습니다. AI 기능이 제한됩니다.")

st.title("💬 카카오톡 연도별 대화 분석 (Ultimate)")

# 데이터 추출 방법 안내
st.markdown("""
### 📂 시작하기 전, 데이터 추출 방법 확인

1. 분석하고 싶은 **카카오톡 채팅방**에 접속합니다.
2. 오른쪽 상단 **메뉴(≡)** 아이콘을 클릭합니다.
3. 하단 **설정(톱니바퀴)** 아이콘을 클릭합니다.
4. **대화 내용 관리 > 대화 내용 저장**을 클릭합니다.
5. 저장된 텍스트 파일(.txt) 또는 CSV를 아래에 업로드하세요.

---
""")

uploaded_files = st.file_uploader("📤 카카오톡 CSV 파일 업로드", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    df = load_data(uploaded_files)
    if not df.empty:
        all_years = sorted(df['Year'].dropna().astype(int).unique())
        if all_years:
            selected_year = st.selectbox("📅 분석할 연도 선택", all_years, index=len(all_years)-1)
            year_df = df[df['Year'] == selected_year]
            
            # 탭 구성 (총 6개)
            tabs = st.tabs(["🎁 Wrapped", "🎭 성격 분석", "🤖 심층 리포트", "📊 발화량", "☁️ 키워드", "📋 데이터"])
            
            with tabs[0]: show_wrapped_ui(year_df, selected_year, api_key)
            with tabs[1]: show_personality_analysis(year_df, api_key)
            with tabs[2]: show_ai_report_ui(year_df, selected_year, api_key)
            
            with tabs[3]: # 발화량
                st.subheader("사용자별 통계")
                uc = year_df['User'].value_counts().reset_index()
                uc.columns = ['User', 'Count']
                st.plotly_chart(px.bar(uc, x='User', y='Count', color='User'), use_container_width=True)
            
            with tabs[4]: # 키워드
                st.subheader("주요 키워드")
                if st.button("키워드 분석 시작"):
                    nouns = extract_nouns(year_df['Message'].dropna().tolist())
                    keyword_df = pd.DataFrame(nouns, columns=['단어', '빈도']).head(30)
                    
                    # 막대 그래프로 표시
                    fig = px.bar(keyword_df, x='빈도', y='단어', orientation='h',
                                title='Top 30 키워드', 
                                color='빈도',
                                color_continuous_scale='Blues')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 데이터프레임으로도 표시
                    st.dataframe(keyword_df, use_container_width=True)
            
            with tabs[5]: st.dataframe(year_df) # 원본 데이터
        else: st.warning("연도 정보 없음")
    else: st.warning("데이터 로드 실패")
else: 
    st.info("👆 위의 안내에 따라 카카오톡 대화 파일을 추출한 후, CSV 파일을 업로드해주세요.")

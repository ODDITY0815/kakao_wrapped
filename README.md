# 💬 카카오톡 대화 분석기 (PC)

카카오톡 대화방의 CSV 파일을 업로드하여 연도별 대화 패턴, 사용자 성격, 주요 키워드 등을 AI 기반으로 분석하는 Streamlit 웹 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 목차

- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [핵심 로직](#-핵심-로직)
- [프로젝트 구조](#-프로젝트-구조)
- [API 키 설정](#-api-키-설정)
- [스크린샷](#-스크린샷)
- [라이선스](#-라이선스)

---

## 🎯 주요 기능

### 1. 🎁 Wrapped (연말결산)
- **총 대화 수**: 선택한 연도의 전체 메시지 개수
- **올해의 MVP**: 가장 많이 대화한 사용자와 지분율
- **올해의 단어**: 가장 많이 언급된 키워드
- **황금 시간대**: 가장 활발하게 대화한 시간대 (아침/오후/저녁/올빼미족 분류)
- **최고의 날**: 하루 최다 메시지를 기록한 날짜
- **AI 키워드 요약**: Gemini AI가 대화 주제 5가지를 자동 추출

### 2. 🎭 성격 분석 (AI 부캐 프로필)
- **MBTI 예측**: 대화 패턴 기반 성격 유형 분석
- **RPG 칭호**: 유머러스한 캐릭터 칭호 부여 (예: 팩트살인마, 이모티콘 마스터)
- **특수 능력**: 각 사용자의 고유한 대화 스타일 (예: 읽씹하기, 3초컷 답장)
- **동물 이모지**: 성격에 맞는 동물 캐릭터 매칭
- **키워드 태그**: 사용자별 대화 특징을 태그로 표현

### 3. 🤖 심층 리포트
- **대화 분위기 분석**: 유머러스, 진지함, 정보공유 등 톤 파악
- **주요 관심사**: 가장 많이 이야기한 토픽 3~4가지 추출
- **한 줄 총평**: 해당 연도 대화를 요약하는 멋진 문구 생성

### 4. 💬 챗봇 (대화 검색)
- **자연어 질문**: "누가 여기 가자고 했어?", "언제 만나기로 했지?" 등 자유롭게 질문
- **컨텍스트 기반 답변**: 실제 대화 내용에서 관련 메시지 검색 후 답변
- **날짜/시간 정보 제공**: 누가, 언제, 무엇을 말했는지 명확하게 표시
- **대화 히스토리**: 이전 질문과 답변을 세션에 저장하여 연속 대화 가능

### 5. 📊 발화량 분석
- **사용자별 메시지 개수**: 막대 그래프로 시각화
- **Plotly 인터랙티브 차트**: 줌, 호버 등 상호작용 가능

### 6. ☁️ 키워드 분석
- **명사 추출**: KoNLPy(Okt) 형태소 분석기로 2글자 이상 명사 추출
- **Top 30 키워드**: 빈도순으로 정렬된 막대 그래프
- **데이터 테이블**: 키워드와 빈도를 표 형식으로 제공

### 7. 📋 데이터 뷰어
- **원본 데이터 조회**: 업로드한 CSV 파일의 전체 내용을 DataFrame으로 표시
- **필터링 및 정렬**: Streamlit 기본 테이블 기능 활용

---

## 🛠 기술 스택

### Frontend
- **Streamlit**: 웹 UI 프레임워크
- **Plotly Express**: 인터랙티브 차트 라이브러리
- **Custom CSS**: HTML/CSS를 통한 카드형 UI 디자인

### Backend & Data Processing
- **Pandas**: CSV 데이터 로드 및 전처리
- **KoNLPy (Okt)**: 한국어 형태소 분석 및 명사 추출
- **Collections (Counter)**: 키워드 빈도 계산

### AI & NLP
- **Google Generative AI (Gemini 2.5 Flash)**: 
  - 주제 분석
  - 성격 프로필 생성
  - 심층 리포트 작성
  - 챗봇 질의응답

---

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/kakao-chat-analyzer.git
cd kakao-chat-analyzer
코드 복사
2. 가상환경 생성 (선택사항)
BASH
코드 복사
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
코드 복사
3. 의존성 설치
BASH
코드 복사
pip install -r requirements.txt
코드 복사
requirements.txt 내용:

코드 복사
streamlit>=1.28.0
pandas>=2.0.0
konlpy>=0.6.0
google-generativeai>=0.3.0
plotly>=5.17.0
코드 복사
4. KoNLPy 추가 설정 (필수)
Windows: Java JDK 설치 필요
Mac: brew install java
Linux: sudo apt-get install openjdk-11-jdk
🚀 사용 방법
1. 카카오톡 대화 내용 추출
카카오톡 PC 버전 실행
분석할 채팅방 접속
오른쪽 상단 메뉴(≡) → 채팅방 설정
대화 내용 관리 → 대화 내용 저장 → 텍스트 파일로 저장
CSV 파일로 저장됨
2. 애플리케이션 실행
BASH
코드 복사
streamlit run app.py
코드 복사
3. 브라우저에서 접속
자동으로 http://localhost:8501 열림
CSV 파일 업로드
분석할 연도 선택
원하는 탭에서 기능 사용

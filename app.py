"""
간단한 주식 대시보드 예제 (Streamlit)
------------------------------------
키움 HTS의 '4x4 멀티차트' 화면처럼, 여러 종목의 차트를 격자로 보여주는
가장 기본적인 형태입니다.

상단: 해외지수·선물·원자재·환율 9종
하단: 스크린샷에 있던 국내 섹터 ETF 16종

실행 방법:
    1) pip install streamlit finance-datareader yfinance plotly
    2) streamlit run app.py
    3) 터미널에 뜨는 http://localhost:8501 주소를 브라우저로 열면 끝

※ 코스피200 야간선물, 코스피 VIX(V-KOSPI200)는 무료 공개 API로는
   안정적으로 구할 방법이 없어 이번 버전에는 포함하지 않았습니다.
"""

import streamlit as st
import FinanceDataReader as fdr
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── 기본 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="내 주식 대시보드", layout="wide")
st.title("📊 내 주식 대시보드")

DAYS_BACK_OPTIONS = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365}

# 상단: 해외지수·선물·원자재·환율 (source: "fdr" 또는 "yf")
TOP_INDICATORS = [
    {"code": "^SOX",   "name": "필라델피아 반도체지수", "source": "yf"},
    {"code": "DJI",    "name": "다우존스",             "source": "fdr"},
    {"code": "^NDX",   "name": "나스닥100",            "source": "yf"},
    {"code": "ES=F",   "name": "S&P500 선물",          "source": "yf"},
    {"code": "NQ=F",   "name": "나스닥100 선물",        "source": "yf"},
    {"code": "GC=F",   "name": "국제 금가격",           "source": "yf"},
    {"code": "CL=F",   "name": "WTI 선물",             "source": "yf"},
    {"code": "USD/KRW","name": "원달러 환율",           "source": "fdr"},
    {"code": "^TNX",   "name": "미국채 10년물",         "source": "yf"},
]

# 하단: 국내 섹터 ETF 16종 (키움 HTS 스크린샷과 동일한 순서)
SECTOR_ETFS = [
    {"code": "KS11",   "name": "종합(KOSPI)",       "source": "fdr"},
    {"code": "KQ11",   "name": "종합(KOSDAQ)",      "source": "fdr"},
    {"code": "091160", "name": "KODEX 반도체",       "source": "fdr"},
    {"code": "305720", "name": "KODEX 2차전지산업",   "source": "fdr"},
    {"code": "102970", "name": "KODEX 증권",         "source": "fdr"},
    {"code": "445290", "name": "KODEX 로봇액티브",    "source": "fdr"},
    {"code": "091180", "name": "KODEX 자동차",       "source": "fdr"},
    {"code": "307520", "name": "TIGER 지주회사",      "source": "fdr"},
    {"code": "466920", "name": "SOL 조선TOP3플러스",  "source": "fdr"},
    {"code": "228790", "name": "TIGER 화장품",        "source": "fdr"},
    {"code": "117700", "name": "KODEX 건설",         "source": "fdr"},
    {"code": "434730", "name": "HANARO 원자력iSelect","source": "fdr"},
    {"code": "491820", "name": "HANARO 전력설비투자", "source": "fdr"},
    {"code": "132030", "name": "KODEX 골드선물(H)",   "source": "fdr"},
    {"code": "463250", "name": "TIGER K방산&우주",    "source": "fdr"},
    {"code": "463050", "name": "TIME K바이오액티브",  "source": "fdr"},
]


# ── 조회 기간 선택 (기본값: 3개월) ─────────────────────────
period_label = st.selectbox(
    "조회 기간", list(DAYS_BACK_OPTIONS.keys()), index=1  # index=1 → "3개월"
)
DAYS_BACK = DAYS_BACK_OPTIONS[period_label]


# ── 데이터 가져오기 (캐시로 반복 호출 줄임) ──────────────────
@st.cache_data(ttl=300)  # 5분 동안 캐시 유지
def fetch_data(code: str, source: str, days_back: int):
    start = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    if source == "yf":
        df = yf.Ticker(code).history(start=start)
        # 타임존 정보 제거 (plotly 표시 편의를 위해)
        df.index = df.index.tz_localize(None)
    else:
        df = fdr.DataReader(code, start)
    return df


# ── 종목 하나를 카드(차트+등락률)로 그리는 함수 ───────────────
def render_card(code: str, name: str, source: str):
    df = fetch_data(code, source, DAYS_BACK)
    if df.empty:
        st.warning(f"{name}: 데이터 없음")
        return

    last = df.iloc[-1]
    prev = df.iloc[-2]
    change = last["Close"] - prev["Close"]
    pct = change / prev["Close"] * 100
    color = "red" if change >= 0 else "blue"  # 국내 관행: 상승=빨강, 하락=파랑

    # 헤더: 종목명 + 현재가 + 등락률
    st.markdown(
        f"**{name}**  \n"
        f"<span style='font-size:22px'>{last['Close']:,.2f}</span> "
        f"<span style='color:{color}'>({change:+,.2f} / {pct:+.2f}%)</span>",
        unsafe_allow_html=True,
    )

    # 캔들 차트
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                increasing_line_color="red",
                decreasing_line_color="blue",
            )
        ]
    )
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )
    st.plotly_chart(fig, width="stretch", key=f"{source}_{code}")


# ── 격자(그리드) 레이아웃으로 배치하는 함수 ─────────────────
def render_grid(items: list, cols_per_row: int = 4):
    for i in range(0, len(items), cols_per_row):
        row_items = items[i : i + cols_per_row]
        cols = st.columns(len(row_items))
        for col, item in zip(cols, row_items):
            with col:
                render_card(item["code"], item["name"], item["source"])


# ── 화면 구성 ─────────────────────────────────────────────
st.subheader("🌍 해외지수 · 선물 · 원자재 · 환율")
render_grid(TOP_INDICATORS, cols_per_row=3)

st.divider()

st.subheader("🇰🇷 국내 섹터 ETF")
render_grid(SECTOR_ETFS, cols_per_row=4)

st.caption(
    "데이터 출처: FinanceDataReader, Yahoo Finance(yfinance) · 5분 간격으로 자동 캐시 갱신 · "
    "코스피200 야간선물 / 코스피 VIX(V-KOSPI200)는 무료 API 미제공으로 제외"
)

"""
간단한 주식 대시보드 예제 (Streamlit)
------------------------------------
키움 HTS의 '4x4 멀티차트' 화면처럼, 여러 종목의 차트를 격자로 보여주는
가장 기본적인 형태입니다. 스크린샷에 있던 섹터 ETF 14개를 그대로 넣었어요.

실행 방법:
    1) pip install streamlit finance-datareader plotly
    2) streamlit run app.py
    3) 터미널에 뜨는 http://localhost:8501 주소를 브라우저로 열면 끝

기존에 쓰시던 FinanceDataReader, pykrx 코드를 이 구조 안에
그대로 끼워 넣으시면 됩니다 (fetch_data 함수만 바꾸면 됨).
"""

import streamlit as st
import FinanceDataReader as fdr
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── 기본 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="내 주식 대시보드", layout="wide")
st.title("📊 내 주식 대시보드")

# 격자에 표시할 종목들 (코드: 표시 이름)
# 키움 HTS 스크린샷과 동일한 순서: 지수 2개 + 섹터 ETF 14개 (종목코드는 각 운용사 공시 기준으로 확인함)
WATCHLIST = {
    "KS11": "종합(KOSPI)",
    "KQ11": "종합(KOSDAQ)",
    "091160": "KODEX 반도체",
    "305720": "KODEX 2차전지산업",
    "102970": "KODEX 증권",
    "445290": "KODEX 로봇액티브",
    "091180": "KODEX 자동차",
    "307520": "TIGER 지주회사",
    "466920": "SOL 조선TOP3플러스",
    "228790": "TIGER 화장품",
    "117700": "KODEX 건설",
    "434730": "HANARO 원자력iSelect",
    "491820": "HANARO 전력설비투자",
    "132030": "KODEX 골드선물(H)",
    "463250": "TIGER K방산&우주",
    "463050": "TIME K바이오액티브",
}

DAYS_BACK = 365  # 최근 1년치 데이터


# ── 데이터 가져오기 (캐시로 반복 호출 줄임) ──────────────────
@st.cache_data(ttl=300)  # 5분 동안 캐시 유지
def fetch_data(code: str):
    start = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
    df = fdr.DataReader(code, start)
    return df


# ── 종목 하나를 카드(차트+등락률)로 그리는 함수 ───────────────
def render_card(code: str, name: str):
    df = fetch_data(code)
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
        f"<span style='font-size:22px'>{last['Close']:,.0f}</span> "
        f"<span style='color:{color}'>({change:+,.0f} / {pct:+.2f}%)</span>",
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
    st.plotly_chart(fig, width="stretch", key=code)


# ── 격자(그리드) 레이아웃으로 배치 ──────────────────────────
codes = list(WATCHLIST.items())
cols_per_row = 4  # 한 줄에 몇 개씩 보여줄지 (HTS 4x4 화면과 동일하게 설정)

for i in range(0, len(codes), cols_per_row):
    row_items = codes[i : i + cols_per_row]
    cols = st.columns(len(row_items))
    for col, (code, name) in zip(cols, row_items):
        with col:
            render_card(code, name)

st.caption("데이터 출처: FinanceDataReader · 5분 간격으로 자동 캐시 갱신")

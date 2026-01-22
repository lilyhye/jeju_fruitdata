import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="제주 상점 분석 플랫폼", layout="wide")

# 데이터 로드 환경 설정
DATA_PATH = r'C:\Users\JMC003\Desktop\icb6_20260103\project_1\jeju_store_cleaned.csv'

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['주문일'] = pd.to_datetime(df['주문일'])
    # 결측 처리
    df['셀러명'] = df['셀러명'].fillna('Unknown')
    df['크기'] = df['크기'].fillna('미분류')
    df['중량'] = df['중량'].fillna('미표기')
    return df

# 기본 데이터 로드
df_raw = load_data()

# --- 사이드바 및 필터 ---
st.sidebar.header("🔍 통합 필터")

# 날짜 범위 필터
min_date = df_raw['주문일'].min().date()
max_date = df_raw['주문일'].max().date()
date_range = st.sidebar.date_input("주문 기간 선택", [min_date, max_date], min_value=min_date, max_value=max_date)

# 필터 항목 리스트
fruits = sorted(df_raw['과일명'].unique())
sizes = sorted(df_raw['크기'].unique())
weights = sorted(df_raw['중량'].unique())
regions = sorted(df_raw['지역'].unique())
sellers = sorted(df_raw['셀러명'].unique())

selected_fruits = st.sidebar.multiselect("과일 품목", fruits, default=fruits)
selected_sizes = st.sidebar.multiselect("크기", sizes, default=sizes)
selected_weights = st.sidebar.multiselect("중량", weights, default=weights)
selected_regions = st.sidebar.multiselect("지역", regions, default=regions)

# 데이터 필터링 적용
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range if not isinstance(date_range, (list, tuple)) else date_range[0]

mask = (df_raw['주문일'].dt.date >= start_date) & (df_raw['주문일'].dt.date <= end_date) & \
       (df_raw['과일명'].isin(selected_fruits)) & (df_raw['크기'].isin(selected_sizes)) & \
       (df_raw['중량'].isin(selected_weights)) & (df_raw['지역'].isin(selected_regions))
df = df_raw[mask].copy()

# --- 탭 구성 ---
tab1, tab2 = st.tabs(["📈 실적 대시보드", "📊 기초 EDA 분석"])

# --- TAB 1: 실적 대시보드 ---
with tab1:
    st.title("🍊 제주 상점 실적 대시보드")
    
    # KPI 지표
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("총 매출액", f"₩{df['결제금액(상품별)'].sum():,.0f}")
    with col2: st.metric("총 주문건수", f"{len(df):,} 건")
    with col3: st.metric("평균 마진율", f"{(df['마진'].sum()/df['결제금액(상품별)'].sum()*100 if not df.empty else 0):.1f}%")
    with col4: st.metric("활동 셀러 수", f"{df['셀러명'].nunique()} 명")
    
    st.divider()
    
    # 셀러 트렌드 비교
    st.subheader("�‍🌾 셀러별 매출 트렌드 비교")
    selected_sellers = st.multiselect("비교할 셀러 선택", sellers, default=sellers[:3])
    if selected_sellers:
        seller_df = df[df['셀러명'].isin(selected_sellers)].copy()
        seller_df['일자'] = seller_df['주문일'].dt.date
        seller_daily = seller_df.groupby(['일자', '셀러명'])['결제금액(상품별)'].sum().reset_index()
        fig_seller = px.line(seller_daily, x='일자', y='결제금액(상품별)', color='셀러명', markers=True)
        st.plotly_chart(fig_seller, use_container_width=True)
    
    # 메인 차트 2종 (실적 중심)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 일자별 매출 및 마진")
        daily_stats = df.groupby(df['주문일'].dt.date).agg({'결제금액(상품별)': 'sum', '마진': 'sum'}).reset_index()
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Scatter(x=daily_stats['주문일'], y=daily_stats['결제금액(상품별)'], name='매출액'))
        fig_dual.add_trace(go.Bar(x=daily_stats['주문일'], y=daily_stats['마진'], name='마진액'))
        st.plotly_chart(fig_dual, use_container_width=True)
    with c2:
        st.subheader("🍎 품목별 매출 비중")
        fig_pie = px.sunburst(df, path=['과일명', '크기'], values='결제금액(상품별)')
        st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 2: 기초 EDA 분석 ---
with tab2:
    st.title("📊 기초 데이터 탐색 (EDA)")
    st.markdown("데이터의 분포와 통계적 특성을 다각도로 분석합니다.")
    
    # --- 그래프 5가지 이상 ---
    st.subheader("🔍 주요 시각화 분석")
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        # 1. 요일별 주문 분포
        df['요일'] = df['주문일'].dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        fig_dow = px.histogram(df, x='요일', category_orders={'요일': weekday_order}, title="1. 요일별 주문 건수")
        st.plotly_chart(fig_dow, use_container_width=True)
        
        # 2. 결제수단별 비중
        fig_pay = px.pie(df, names='결제방법', title="2. 결제수단 비중", hole=0.4)
        st.plotly_chart(fig_pay, use_container_width=True)
        
        # 3. 마진 vs 결제금액 상관관계
        fig_scatter = px.scatter(df, x='결제금액(상품별)', y='마진', color='과일명', hover_data=['상품명'], title="3. 결제금액 대비 마진 상관관계")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with g_col2:
        # 4. 시간대별 주문 히트맵 (시간 데이터가 있다면)
        df['시간'] = df['주문일'].dt.hour
        fig_hour = px.histogram(df, x='시간', title="4. 시간대별 주문 분포", nbins=24)
        st.plotly_chart(fig_hour, use_container_width=True)
        
        # 5. 지역별 마진율 BoxPlot
        df['마진율'] = (df['마진'] / df['결제금액(상품별)'] * 100)
        fig_box = px.box(df, x='지역', y='마진율', title="5. 지역별 마진율 분포")
        st.plotly_chart(fig_box, use_container_width=True)
        
        # 6. 품목별 평균 주문수량
        qty_stats = df.groupby('과일명')['주문수량'].mean().reset_index()
        fig_qty = px.bar(qty_stats, x='과일명', y='주문수량', title="6. 품목별 평균 주문수량")
        st.plotly_chart(fig_qty, use_container_width=True)
        
        # 7. 회원/비회원 재구매율 분석
        st.write("---")
        # 고객 식별자 생성 (이름 + 연락처)
        df['고객ID'] = df['주문자명'] + df['주문자연락처'].astype(str)
        
        # 회원구분별 고객 구매 횟수 집계
        cust_counts = df.groupby(['회원구분', '고객ID']).size().reset_index(name='구매횟수')
        
        # 재구매자 정의 (구매횟수 > 1)
        repur_stats = cust_counts.groupby('회원구분').agg(
            전체고객수=('고객ID', 'nunique'),
            재구매고객수=('고객ID', lambda x: (cust_counts.loc[cust_counts['고객ID'].isin(x), '구매횟수'] > 1).sum())
        ).reset_index()
        
        # 재구매율 계산
        repur_stats['재구매율(%)'] = (repur_stats['재구매고객수'] / repur_stats['전체고객수']) * 100
        
        fig_repur = px.bar(repur_stats, x='회원구분', y='재구매율(%)', color='회원구분', 
                           text=repur_stats['재구매율(%)'].apply(lambda x: f'{x:.1f}%'),
                           title="7. 회원구분별 재구매율 비교")
        st.plotly_chart(fig_repur, use_container_width=True)

    st.divider()
    
    # --- 표 (통계 데이터) 5가지 이상 ---
    st.subheader("📑 통계 데이터 테이블")
    
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        st.write("**1. 품목별 주요 통계**")
        st.dataframe(df.groupby('과일명').agg({'결제금액(상품별)':['sum','mean','max'], '마진':['sum','mean']}).style.format("{:,.0f}"))
        
        st.write("**2. 지역별 매출 순위**")
        st.dataframe(df.groupby('지역')['결제금액(상품별)'].sum().sort_values(ascending=False).reset_index().head(10))
        
        st.write("**3. 결제방법별 평균 결제금액**")
        st.dataframe(df.groupby('결제방법')['결제금액(상품별)'].mean().reset_index().rename(columns={'결제금액(상품별)':'평균결제금액'}))

    with t_col2:
        st.write("**4. 셀러별 마진 기여도 (Top 10)**")
        st.dataframe(df.groupby('셀러명')['마진'].sum().sort_values(ascending=False).head(10))
        
        st.write("**5. 크기/중량 조합별 주문 빈도**")
        st.dataframe(pd.crosstab(df['크기'], df['중량']))
        
        st.write("**6. 회원구분별 매출 비중**")
        st.dataframe(df.groupby('회원구분')['결제금액(상품별)'].sum().reset_index())

# 상세 데이터 보기
if st.sidebar.checkbox("원본 데이터 탐색"):
    st.divider()
    st.subheader("📑 필터링된 원본 데이터 항목")
    st.dataframe(df)

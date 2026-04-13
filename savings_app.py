import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. 系統設定與樣式 ---
st.set_page_config(page_title="存錢目標管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2e7d32; }
    .success-text { color: #2e7d32; font-weight: 800; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

DB_TASKS = "savings_tasks.csv"
DB_LOGS = "savings_logs.csv"

# --- 2. 登入驗證 ---
if "auth_savings" not in st.session_state: st.session_state.auth_savings = False
if not st.session_state.auth_savings:
    st.title("🔐 個人資產隱私防線")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("驗證登入"):
        if pwd == "085799": st.session_state.auth_savings = True; st.rerun()
        else: st.error("密碼錯誤")
    st.stop()

# --- 3. 側邊欄 ---
with st.sidebar:
    st.title("💰 存錢控制台")
    if st.button("🔓 安全登出"): st.session_state.auth_savings = False; st.rerun()
    st.divider()
    st.subheader("🆕 建立新目標")
    with st.form("new_task_form", clear_on_submit=True):
        t_name = st.text_input("任務名稱 (如：買房首期)")
        t_goal = st.number_input("目標金額", min_value=1.0, step=1000.0)
        if st.form_submit_button("新增目標表"):
            if t_name:
                clean_name = t_name.strip()
                new_t = pd.DataFrame([{"任務名稱": clean_name, "目標金額": t_goal}])
                if os.path.exists(DB_TASKS):
                    pd.concat([pd.read_csv(DB_TASKS), new_t], ignore_index=True).to_csv(DB_TASKS, index=False)
                else: new_t.to_csv(DB_TASKS, index=False)
                st.rerun()

# --- 4. 主畫面 ---
st.title("🎯 我的存錢目標清單")

if not os.path.exists(DB_TASKS):
    st.info("目前還沒有建立任何目標。")
else:
    tasks_df = pd.read_csv(DB_TASKS)
    logs_df = pd.read_csv(DB_LOGS) if os.path.exists(DB_LOGS) else pd.DataFrame(columns=['任務名稱', '日期', '存入金額'])
    
    if not logs_df.empty:
        logs_df['任務名稱'] = logs_df['任務名稱'].astype(str).str.strip()
        logs_df['存入金額'] = pd.to_numeric(logs_df['存入金額'], errors='coerce').fillna(0)

    for idx, row in tasks_df.iterrows():
        current_name = str(row['任務名稱']).strip()
        target_amt = float(row['目標金額'])
        
        relevant_logs = logs_df[logs_df['任務名稱'] == current_name]
        current_sum = float(relevant_logs['存入金額'].sum())
        
        # --- 修正計算邏輯：小數點後 3 位 ---
        # 達成率計算至小數點後 3 位
        progress_pct = round((current_sum / target_amt) * 100, 3) if target_amt > 0 else 0.0
        # 剩餘進度固定為 100 減去達成率，同樣取小數點 3 位
        remain_pct = round(100.0 - progress_pct, 3) if progress_pct < 100 else 0.0
        
        with st.container():
            st.markdown(f"### 🚩 {current_name}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("目前金額", f"${int(current_sum):,}")
            c2.metric("目標金額", f"${int(target_amt):,}")
            
            if current_sum >= target_amt:
                c3.markdown("<p class='success-text'>✅ 進度已達標</p>", unsafe_allow_html=True)
                c4.metric("剩餘進度", "0%")
            else:
                c3.metric("已達成", f"{progress_pct}%")
                c4.metric("剩餘進度", f"{remain_pct}%")
            
            st.progress(min(1.0, current_sum / target_amt) if target_amt > 0 else 0.0)
            
            exp = st.expander("⚙️ 紀錄維護與刪除目標")
            ec1, ec2 = exp.columns([1, 2])
            with ec1:
                st.write("➕ 新增存款")
                s_date = st.date_input("日期", datetime.now(), key=f"d_{idx}")
                s_amt = st.number_input("金額", min_value=1.0, key=f"a_{idx}")
                if st.button("確認存入", key=f"b_{idx}"):
                    new_entry = pd.DataFrame([{"任務名稱": current_name, "日期": s_date.strftime("%Y-%m-%d"), "存入金額": s_amt}])
                    if os.path.exists(DB_LOGS):
                        pd.concat([pd.read_csv(DB_LOGS), new_entry], ignore_index=True).to_csv(DB_LOGS, index=False)
                    else: new_entry.to_csv(DB_LOGS, index=False)
                    st.rerun()
            
            with ec2:
                st.write("📜 歷史紀錄")
                st.dataframe(relevant_logs[['日期', '存入金額']].sort_values("日期", ascending=False), hide_index=True, use_container_width=True)
            
            if exp.button(f"🗑️ 永久刪除目標表", key=f"del_{idx}"):
                tasks_df.drop(idx).to_csv(DB_TASKS, index=False)
                if os.path.exists(DB_LOGS):
                    logs_df[logs_df['任務名稱'] != current_name].to_csv(DB_LOGS, index=False)
                st.rerun()
        st.divider()
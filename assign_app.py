import streamlit as st
import pandas as pd
import json
# -*- coding: utf-8 -*-
from assign_automation import run_batch_assignment  # 必須


st.set_page_config(page_title="Amazon 配送 自動割当ツール", layout="centered")
st.title("🚚 Amazon 配送 自動割当ツール")

st.markdown("Excelファイル（Tracking ID）とドライバーマスターをアップロードしてください。")

# --- ファイルアップロード ---
uploaded_file = st.file_uploader("📄 Excelファイル（B列にTracking ID、シート名にコース番号）", type=["xlsx"])
driver_master_file = st.file_uploader("📄 ドライバーマスター（drivers_master.csv）", type=["csv"])

def extract_tracking_ids(sheet_df):
    return sheet_df.iloc[3:, 1].dropna().astype(str).tolist()  # B列（index=1）

def get_course_from_sheet_name(sheet_name):
    return sheet_name.split("_")[-1] if "_" in sheet_name else sheet_name

# 入力フォーム
st.markdown("### 🔢 コース名とドライバー名の組み合わせ（最大20名）")
assignments = []
for i in range(1, 21):
    cols = st.columns([1, 2, 2])
    with cols[0]:
        st.markdown(f"#### {i}")
    with cols[1]:
        course = st.text_input(f"コース名{i}", key=f"course_{i}")
    with cols[2]:
        driver = st.text_input(f"ドライバー名{i}", key=f"driver_{i}")
    if course.strip() and driver.strip():
        assignments.append({"course": course.strip(), "driver": driver.strip()})

# テストモード
is_test_mode = st.checkbox("✅ テストモード（Seleniumで割当は行いません）", value=True)

# 実行ボタン
if st.button("🚀 実行開始（Selenium含む）"):
    if not uploaded_file:
        st.error("⚠️ Excelファイルをアップロードしてください。")
    elif not assignments:
        st.error("⚠️ コース名とドライバー名を1件以上入力してください。")
    else:
        xls = pd.ExcelFile(uploaded_file)
        execution_pairs = []

        for sheet_name in xls.sheet_names:
            course_code = get_course_from_sheet_name(sheet_name)
            df = xls.parse(sheet_name, header=None)
            tracking_ids = extract_tracking_ids(df)

            for a in assignments:
                if a["course"] == course_code:
                    for tid in tracking_ids:
                        execution_pairs.append({
                            "tracking_id": tid,
                            "driver_name": a["driver"]
                        })

        if not execution_pairs:
            st.warning("⚠️ 一致するコース名が見つかりませんでした。")
        else:
            st.success("✅ データ準備完了！Seleniumで処理を実行します。")
            run_batch_assignment(execution_pairs, test_mode=is_test_mode)
            st.success("🎉 処理が完了しました！")

import streamlit as st
import pandas as pd
import io
import subprocess
import json

st.set_page_config(page_title="Amazon 配送 自動割当ツール", layout="centered")
st.title("🚚 Amazon 配送 自動割当ツール")

st.markdown("""
Excelファイルをアップロードしてください（B列にTracking ID、シート名にコース番号）
""")

# --- ファイルアップロード ---
uploaded_file = st.file_uploader("Excelファイルをアップロード（B列にTracking ID）", type=["xlsx"])

# --- drivers_master.csv アップロード ---
driver_master_file = st.file_uploader("ドライバーマスターをアップロード（drivers_master.csv）", type=["csv"])

def extract_tracking_ids(sheet_df):
    return sheet_df.iloc[3:, 1].dropna().astype(str).tolist()  # B列（index 1）の4行目以降

def get_course_from_sheet_name(sheet_name):
    if "_" in sheet_name:
        return sheet_name.split("_")[-1]
    return sheet_name

# 入力フォーム
st.markdown("### 🔢 コース名とドライバー名の組み合わせ（最大20名分）")
assignments = []

for i in range(1, 21):
    cols = st.columns([1, 2, 2])
    with cols[0]:
        st.markdown(f"#### {i}")
    with cols[1]:
        course = st.text_input(f"コース名{i}", key=f"course_{i}")
    with cols[2]:
        driver = st.text_input(f"ドライバー名{i}（例：翔平 宮前）", key=f"driver_{i}")
    if course.strip() != "" and driver.strip() != "":
        assignments.append({"course": course.strip(), "driver": driver.strip()})

# テストモード
is_test_mode = st.checkbox("✅ テストモード（Assignは実行しません）", value=True)

# 実行ボタン
if st.button("実行開始"):
    if not uploaded_file:
        st.error("Excelファイルをアップロードしてください。")
    elif not assignments:
        st.error("少なくとも1つのコース名とドライバー名を入力してください。")
    else:
        # Excel読み込み
        xls = pd.ExcelFile(uploaded_file)
        results = []

        for sheet_name in xls.sheet_names:
            course_code = get_course_from_sheet_name(sheet_name)
            df = xls.parse(sheet_name, header=None)
            tracking_ids = extract_tracking_ids(df)

            for a in assignments:
                if a["course"] == course_code:
                    results.append({
                        "course": course_code,
                        "driver": a["driver"],
                        "tracking_ids": tracking_ids
                    })

        if not results:
            st.warning("一致するコース名が見つかりませんでした。シート名と一致しているか確認してください。")
        else:
            for r in results:
                st.markdown(f"### 🚛 {r['course']} - {r['driver']}")
                st.write(r['tracking_ids'])
            st.success("読み込み完了！Seleniumでの処理を実行します。")

            # --- JSON一時保存 ---
            with open("input_data.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            # --- Seleniumスクリプトを呼び出す ---
            cmd = ["python", "assign_automation.py", "--input", "input_data.json", "--test", str(is_test_mode)]
            subprocess.run(cmd)

            st.success("Selenium処理が完了しました。")

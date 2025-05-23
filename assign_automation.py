from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# --- Streamlitから呼び出す用の関数（先に定義）
def run_batch_assignment(pairs, test_mode=True):
    """
    pairs: List of dicts
    e.g. [{"tracking_id": "TST123", "driver_name": "山田 太郎"}, ...]
    """
    driver = launch_chrome_temp()
    for pair in pairs:
        process_assignment(driver, pair["tracking_id"], pair["driver_name"], test_mode=test_mode)
    input("✅ Enterでブラウザを閉じます...")
    driver.quit()

# --- Chrome起動とログイン待機
def launch_chrome_temp():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=options)

    driver.get("https://www.amazonlogistics.jp/station/dashboard/problemsolvemanage")
    print("🔐 Amazonログインしてください（30秒待機）...")
    time.sleep(30)
    return driver

# --- タブ遷移処理
def go_to_on_road_tab(driver):
    wait = WebDriverWait(driver, 15)
    try:
        iframe = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "iframe[src*='node-exceptions.last-mile.amazon.dev']")
        ))
        driver.switch_to.frame(iframe)
        print("🖐 iframeに切り替え完了")

        on_road_tab = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[normalize-space(text())='On-road management']")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", on_road_tab)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", on_road_tab)
        print("🔹 On-road management タブをJSクリックしました")

        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'Tracking')]")
        ))
        print("✅ On-road タブ表示完了")
    except Exception as e:
        print(f"❌ タブクリックに失敗しました: {e}")

# --- 1件分の割当処理
def process_assignment(driver, tracking_id, driver_name, test_mode=True):
    wait = WebDriverWait(driver, 10)

    go_to_on_road_tab(driver)

    try:
        search_input = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'Tracking')]")))
        search_input.clear()
        search_input.send_keys(tracking_id)
        search_input.send_keys(Keys.RETURN)
        print(f"🔎 トラッキングIDを検索: {tracking_id}")
        time.sleep(3)
    except Exception as e:
        print(f"❌ 検索欄エラー: {e}")
        return

    try:
        checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']")))
        checkbox.click()
        print("✅ 荷物チェックボックスをクリック")
    except Exception as e:
        print(f"❌ 荷物チェックエラー: {e}")
        return

    try:
        edit_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(),'Edit Assignment')]")))
        edit_btn.click()
        print("🚰 Edit Assignment ボタンをクリック")
        time.sleep(2)
    except Exception as e:
        print(f"❌ Edit Assignment エラー: {e}")
        return

    try:
        driver_input = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[contains(@placeholder, 'name or ID')]")))
        driver_input.clear()
        driver_input.send_keys(driver_name)
        print(f"✅ ドライバー名を入力: {driver_name}")
        time.sleep(2)
    except Exception as e:
        print(f"❌ ドライバー入力エラー: {e}")
        return

    if test_mode:
        print("🧪 テストモード中（ここで送信停止）")

# --- CLI実行時のみ動作（Streamlitと共存可能）
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="input_data.json", help="JSON input file")
    parser.add_argument("--test", type=lambda x: x.lower() == "true", default=True, help="テストモード")
    args = parser.parse_args()

    test_mode = args.test

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    assignments = data["assignments"]

    driver = launch_chrome_temp()
    for entry in assignments:
        course = entry["course"]
        driver_name = entry["driver"]
        tracking_ids = entry["tracking_ids"]

        print(f"\n🚚 {course} - {driver_name} の処理を開始")
        for tid in tracking_ids:
            process_assignment(driver, tid, driver_name, test_mode=test_mode)

    input("\n✅ Enterでブラウザを閉じます...")
    driver.quit()

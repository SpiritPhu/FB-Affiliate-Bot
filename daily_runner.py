import json
import os
import time
import schedule
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import importlib

import fb_auth
import fb_auto_post
import fb_auto_comment_group

# Đường dẫn tĩnh
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
EXCEL_PATH = os.path.join(BASE_DIR, "data", "running_lists.xlsx")

# Biến toàn cục lưu trữ các driver
drivers = {}

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def init_all_drivers(config):
    accounts = config.get("accounts_to_run", [])
    if not accounts:
        print("⚠️ Không có tài khoản nào được cấu hình trong config.json")
        return

    for acc in accounts:
        print(f"\n[{acc}] 🚀 Khởi tạo trình duyệt...")
        try:
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            driver = webdriver.Chrome(service=service, options=options)
            
            # Đăng nhập bằng cookies (Giả định cookie đã được tạo trước bằng Streamlit)
            fb_auth.login_to_facebook_with_cookies(driver, acc, "")
            
            drivers[acc] = driver
            print(f"[{acc}] ✅ Trình duyệt khởi động thành công và đang mở.")
        except Exception as e:
            print(f"[{acc}] ❌ Lỗi khởi tạo trình duyệt: {e}")

def get_groups_for_account(account_str):
    try:
        df = pd.read_excel(EXCEL_PATH)
        df["Account"] = df["Account"].astype(str)
        links = df[df["Account"] == account_str]["Link"].dropna().tolist()
        return [str(l).strip() for l in links]
    except Exception as e:
        print(f"Lỗi đọc file Excel cho {account_str}: {e}")
        return []

def daily_job():
    print(f"\n{'='*50}")
    print(f"🔥 BẮT ĐẦU CHẠY CHIẾN DỊCH VÀO LÚC: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    config = load_config()
    post_content = config.get("post_content", "")
    post_image_dir = config.get("post_image_dir", None)
    comment_prompt = config.get("comment_prompt", "")
    comment_image_dir = config.get("comment_image_dir", None)
    wait_minutes = config.get("wait_minutes_between_post_and_comment", 15)
    accounts = config.get("accounts_to_run", [])
    
    successful_links_by_account = {}

    # --- BƯỚC 1: CHẠY AUTO POST CHO TẤT CẢ CÁC TÀI KHOẢN ---
    print("\n[BƯỚC 1: ĐĂNG BÀI - AUTO POST]")
    for acc in accounts:
        if acc not in drivers:
            print(f"[{acc}] ⚠️ Trình duyệt chưa được khởi tạo. Bỏ qua.")
            continue
            
        driver = drivers[acc]
        groups_list = get_groups_for_account(acc)
        
        if not groups_list:
            print(f"[{acc}] ⚠️ Không tìm thấy link nhóm nào trong file Excel.")
            continue
            
        print(f"[{acc}] Bắt đầu Auto Post cho {len(groups_list)} nhóm...")
        try:
            importlib.reload(fb_auto_post)
            post_results = fb_auto_post.auto_post_to_groups_v5(driver, groups_list, post_content, post_image_dir)
            
            # Lọc các link thành công để lưu lại cho bước Comment
            successful_links = [r.get("url") for r in post_results if r.get("status") == "Success"]
            successful_links_by_account[acc] = successful_links
            
            print(f"[{acc}] ✅ Đã đăng bài xong. Thành công: {len(successful_links)}/{len(groups_list)}")
        except Exception as e:
            print(f"[{acc}] ❌ Lỗi Auto Post: {e}")

    # --- BƯỚC 2: NGỦ ĐÔNG GIỮA HAI TÁC VỤ ---
    print(f"\n[BƯỚC 2: ĐỢI {wait_minutes} PHÚT TRƯỚC KHI BÌNH LUẬN]")
    total_seconds = wait_minutes * 60
    for i in range(total_seconds, 0, -1):
        if i % 60 == 0:
            print(f"Đang đợi... còn {i//60} phút")
        time.sleep(1)

    # --- BƯỚC 3: CHẠY AUTO COMMENT CHO TẤT CẢ CÁC TÀI KHOẢN ---
    print("\n[BƯỚC 3: BÌNH LUẬN - AUTO COMMENT]")
    for acc in accounts:
        successful_links = successful_links_by_account.get(acc, [])
        if not successful_links:
            print(f"[{acc}] ⚠️ Không có bài viết nào đăng thành công ở Bước 1 để comment. Bỏ qua.")
            continue
            
        driver = drivers[acc]
        print(f"[{acc}] Bắt đầu Auto Comment cho {len(successful_links)} nhóm...")
        try:
            importlib.reload(fb_auto_comment_group)
            comment_results = fb_auto_comment_group.run_multi_group_commenting(
                driver, 
                group_urls=successful_links,
                max_comments=1,
                image_dir=comment_image_dir,
                pause_between_groups=(20, 30),
                prompt_template=comment_prompt
            )
            print(f"[{acc}] ✅ Đã chạy xong Auto Comment liên hoàn!")
        except Exception as e:
            print(f"[{acc}] ❌ Lỗi Auto Comment: {e}")
            
    print(f"\n{'='*50}")
    print(f"🎉 ĐÃ HOÀN THÀNH CHIẾN DỊCH. TIẾP TỤC NGỦ ĐÔNG CHỜ LẦN CHẠY TIẾP THEO.")
    print(f"{'='*50}")

if __name__ == "__main__":
    print("🚀 KHỞI ĐỘNG HỆ THỐNG DAILY RUNNER...")
    config = load_config()
    
    # 1. Mở tất cả các trình duyệt và giữ nguyên session
    init_all_drivers(config)
    
    # 2. Lên lịch chạy
    run_times = config.get("run_times", ["07:00", "19:00"])
    for t in run_times:
        schedule.every().day.at(t).do(daily_job)
        print(f"🕒 Đã lên lịch chạy tự động vào lúc: {t} hằng ngày")
        
    print("\n💤 Hệ thống đang ngủ đông và chờ đến giờ chạy...")
    
    # 3. Vòng lặp vô hạn giữ chương trình sống
    while True:
        schedule.run_pending()
        time.sleep(1)

import pickle
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_cookie_filename(username):
    # Đảm bảo thư mục 'cookies' tồn tại
    if not os.path.exists("cookies"):
        os.makedirs("cookies")
    # Thay thế các ký tự không hợp lệ cho tên file (nếu có)
    safe_username = "".join([c if c.isalnum() or c in "._-@" else "_" for c in username])
    return os.path.join("cookies", f"facebook_cookies_{safe_username}.pkl")

def save_cookies(driver, filepath):
    """Lưu cookies của trình duyệt vào file bằng pickle."""
    with open(filepath, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print(f"🍪 Đã lưu cookies vào {filepath}")

def load_cookies(driver, filepath):
    """Tải cookies từ file và nạp vào trình duyệt."""
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print(f"🍪 Đã nạp cookies từ {filepath}")
        return True
    return False

def login_to_facebook_with_cookies(driver, username, password):
    """
    Quy trình đăng nhập:
    1. Vào trang facebook.com
    2. Thử nạp cookies cũ, nếu có thì refresh trang.
    3. Kiểm tra xem đã đăng nhập thành công chưa.
    4. Nếu chưa, tiến hành điền username/password để đăng nhập.
    5. Đăng nhập xong thì lưu cookies cho lần sau.
    """
    cookie_filepath = get_cookie_filename(username)
    
    print(f"Mở trang Facebook (sử dụng file cookies: {cookie_filepath})...")
    driver.get("https://facebook.com/")
    time.sleep(2)
    
    # Thử nạp cookie
    if load_cookies(driver, cookie_filepath):
        print("Đang tải lại trang với cookies...")
        driver.refresh()
        time.sleep(5)
        
        # Kiểm tra trạng thái đăng nhập (để ý URL hoặc phần tử)
        if "facebook.com/login" not in driver.current_url:
            print("✅ Đăng nhập thành công bằng cookies!")
            return
        else:
            print("⚠️ Cookies có vẻ đã hết hạn. Bắt đầu đăng nhập bằng mật khẩu...")

    try:
        # Đường dẫn XPath bạn cung cấp (có thể cần cập nhật nếu FB thay đổi giao diện)
        username_xpath = "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div[1]/div/div[1]/div/div/div[1]/input"
        password_xpath = "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div[1]/div/div[2]/div/div/div[1]/input"
        login_btn_xpath = "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div/div/div/div/div/div/div/div/div/div/div[2]/form/div/div[1]/div/div[3]/div/div/div/div[1]"

        # 1. Chờ và điền Username
        print("Đang tìm ô nhập Username...")
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, username_xpath))
        )
        username_field.clear() # Xóa chữ cũ (nếu có)
        username_field.send_keys(username)
        time.sleep(1) # Nghỉ 1 giây
        
        # 2. Chờ và điền Password
        print("Đang tìm ô nhập Password...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, password_xpath))
        )
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1) # Nghỉ 1 giây
        
        # 3. Bấm nút Đăng nhập
        print("Đang bấm nút Đăng nhập...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, login_btn_xpath))
        )
        login_button.click()
        
        print("Đã bấm đăng nhập thành công. Chờ trang tải (10s)...")
        time.sleep(10) # Dừng lại chờ trang web tải sau khi login
        
    except Exception as e:
        print(f"Lỗi khi tự động điền đăng nhập (Có thể giao diện thay đổi): {e}")
        print("Vui lòng tự đăng nhập thủ công trên trình duyệt (bạn có 60 giây)...")
        for _ in range(60):
            if "login" not in driver.current_url and "checkpoint" not in driver.current_url:
                break
            time.sleep(1)

    time.sleep(3)
    if "login" not in driver.current_url and "checkpoint" not in driver.current_url:
        print("Đăng nhập thành công, tiến hành lưu cookies...")
        save_cookies(driver, cookie_filepath)
    else:
        print("Vẫn chưa đăng nhập thành công. Cookies KHÔNG được lưu.")

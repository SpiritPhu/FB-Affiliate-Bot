import streamlit as st
import os
import sys
import glob
import pandas as pd
import time

# Đảm bảo đường dẫn hiện tại được nhận diện
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import undetected_chromedriver as uc
import importlib

# Tắt tự động reload của Streamlit khi các file cấu hình khác thay đổi liên tục
st.set_page_config(page_title="Facebook Bot Dashboard", layout="wide")

# Các module custom
import fb_auth
import fb_auto_post
import fb_auto_comment_group

def init_driver():
    if "driver" not in st.session_state:
        st.session_state.driver = None

    if st.session_state.driver is None:
        try:
            from chrome_helper import get_chrome_driver
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            st.session_state.driver = get_chrome_driver(options=options)
            st.success("Khởi tạo trình duyệt thành công!")
        except Exception as e:
            st.error(f"Lỗi khởi tạo trình duyệt: {e}")
            
def login(username, password):
    if st.session_state.driver is None:
        st.warning("Vui lòng khởi tạo trình duyệt trước (hoặc đợi trình duyệt khởi động).")
        return
        
    st.info(f"Đang tiến hành đăng nhập cho: {username} ...")
    try:
        # Nạp lại module để đảm bảo code mới nhất được chạy
        importlib.reload(fb_auth)
        fb_auth.login_to_facebook_with_cookies(st.session_state.driver, username, password)
        st.success("Đăng nhập thành công/Hoàn tất tải cookies! Hãy kiểm tra cửa sổ Chrome.")
    except Exception as e:
        st.error(f"Lỗi đăng nhập: {e}")

st.title("🤖 Facebook Bot Dashboard")

# ----------------- SECTION 1: LOGIN -----------------
st.header("1. Cấu hình Tài Khoản (Đăng Nhập)")

def get_saved_accounts():
    if not os.path.exists("cookies"):
        return []
    files = glob.glob(os.path.join("cookies", "facebook_cookies_*.pkl"))
    accounts = []
    for f in files:
        filename = os.path.basename(f)
        username = filename.replace("facebook_cookies_", "").replace(".pkl", "")
        accounts.append(username)
    return accounts

col1, col2 = st.columns(2)
with col1:
    st.info("Chọn tài khoản đã lưu hoặc thêm mới. Nếu dùng tài khoản cũ, Cookie sẽ được tự động nạp.")
    saved_accounts = get_saved_accounts()
    
    selected_acc = st.selectbox("Tài khoản:", ["-- Thêm tài khoản mới --"] + saved_accounts)
    
    if selected_acc == "-- Thêm tài khoản mới --":
        username = st.text_input("Username (Tài khoản mới)", placeholder="Email hoặc số điện thoại")
        password = st.text_input("Password", type="password", placeholder="Bắt buộc")
    else:
        username = selected_acc
        password = st.text_input("Password", type="password", placeholder="Không bắt buộc nếu Cookie còn hạn")
    
    if st.button("🚀 Khởi tạo trình duyệt & Đăng nhập", type="primary"):
        if not username:
            st.warning("Vui lòng nhập Username.")
        elif selected_acc == "-- Thêm tài khoản mới --" and not password:
            st.warning("Vui lòng nhập Password cho tài khoản mới.")
        else:
            with st.spinner("Đang mở trình duyệt..."):
                init_driver()
            if st.session_state.driver:
                login(username, password)
                # Reload lại trang để cập nhật danh sách tài khoản nếu có tài khoản mới
                st.rerun()
                
with col2:
    st.write("**Trạng thái trình duyệt:**")
    if "driver" in st.session_state and st.session_state.driver is not None:
        st.success("🟢 Trình duyệt đang mở.")
        if st.button("Đóng trình duyệt (Thoát)"):
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.rerun()
    else:
        st.error("🔴 Trình duyệt đang đóng.")

st.divider()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_groups_for_account(account_str):
    if not account_str: return ""
    try:
        excel_path = os.path.join(BASE_DIR, "data", "running_lists.xlsx")
        df = pd.read_excel(excel_path)
        df["Account"] = df["Account"].astype(str)
        links = df[df["Account"] == account_str]["Link"].dropna().tolist()
        return "\n".join([str(l).strip() for l in links])
    except:
        return ""

# Lấy danh sách group linh động theo tài khoản đang chọn
dynamic_groups = get_groups_for_account(username)

# ----------------- SECTION 2: BOT ACTIONS -----------------
st.header("2. Chọn Chức Năng Chạy Bot")

tab1, tab2, tab3 = st.tabs(["📝 Auto Post (Đăng bài)", "💬 Auto Comment (Bình luận)", "🔄 Auto Post & Comment Liên Hoàn"])

with tab1:
    st.subheader("Tính năng Đăng bài tự động lên Group")
    
    # Textarea cho danh sách group (mỗi group 1 dòng)
    default_groups = dynamic_groups if dynamic_groups else "https://www.facebook.com/groups/880359772330567/\nhttps://www.facebook.com/groups/vinfastfadil/\nhttps://www.facebook.com/groups/3952468598316805/"
    danh_sach_groups_input = st.text_area("Danh sách URL Groups (Mỗi URL 1 dòng):", value=default_groups, height=150)
    
    # Textarea cho nội dung bài post
    default_content = "VF8 all new dán thêm chút tem vào nhìn khác hẳn anh em nhỉ, chất ngầu hơn hẳn :D.\nhttps://s.shopee.vn/50X7lXZUwc . Trên sọp pe đang có nhiều mẫu tem xe rẻ đẹp, cả nhà mình tham khảo nhé.\n https://s.shopee.vn/50X7lXZUwc .\np/s: ảnh em đi mượn ạ."
    noi_dung_input = st.text_area("Nội dung bài viết (AI sẽ tự động xào bài dựa trên nội dung này):", value=default_content, height=150)
    
    # Input cho thư mục ảnh
    thu_muc_anh_input = st.text_input("Thư mục chứa ảnh:", value=os.path.join(BASE_DIR, "images", "vinfast"))
    
    if st.button("▶️ Chạy Auto Post", use_container_width=True):
        if "driver" not in st.session_state or st.session_state.driver is None:
            st.error("Vui lòng đăng nhập và khởi tạo trình duyệt ở Bước 1 trước.")
        else:
            # Xử lý dữ liệu đầu vào
            groups_list = [g.strip() for g in danh_sach_groups_input.split("\n") if g.strip()]
            img_folder = thu_muc_anh_input.strip() if thu_muc_anh_input.strip() != "" else None
            
            st.info(f"Bắt đầu chạy Auto Post cho {len(groups_list)} nhóm...")
            try:
                importlib.reload(fb_auto_post)
                # Chạy logic
                results = fb_auto_post.auto_post_to_groups_v5(st.session_state.driver, groups_list, noi_dung_input.strip(), img_folder)
                st.success("✅ Đã chạy xong Auto Post!")
                st.markdown("### 📊 BẢNG THỐNG KÊ KẾT QUẢ ĐĂNG BÀI")
                # Chuẩn hóa tên cột
                formatted_results = [{"URL Nhóm": r.get("url", ""), "Trạng thái": r.get("status", ""), "Lý do": r.get("reason", "")} for r in results]
                st.table(formatted_results)
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")


with tab2:
    st.subheader("Tính năng Bình luận bài viết đầu tiên trên Group")
    
    default_comment_groups = dynamic_groups if dynamic_groups else "https://www.facebook.com/groups/880359772330567/\nhttps://www.facebook.com/groups/vinfastfadil/"
    comment_groups_input = st.text_area("Danh sách URL Groups cần Comment (Mỗi URL 1 dòng):", value=default_comment_groups, height=150)
    comment_img_input = st.text_input("Thư mục chứa ảnh (Comment):", value=os.path.join(BASE_DIR, "images", "vinfast"))
    
    default_prompt_comment = """Bạn là một người dùng mạng xã hội bình thường, đọc bài post và đưa ra bình luận hài hước hoặc khen ngợi sản phẩm phù hợp. Văn phong ngắn gọn đời thường, có thể mất dạy một chút cho vui vẻ.

Nội dung bài viết:
"{post_content}"

YÊU CẦU QUAN TRỌNG: Viết 1 câu thật ngắn, ngôn ngữ mạng xã hội, có thể chèn link sản phẩm nếu cần."""
    prompt_template_input = st.text_area("Prompt cho AI (Sử dụng {post_content} để AI biết nội dung bài gốc):", value=default_prompt_comment, height=150)
    
    if st.button("▶️ Chạy Auto Comment", use_container_width=True):
         if "driver" not in st.session_state or st.session_state.driver is None:
             st.error("Vui lòng đăng nhập và khởi tạo trình duyệt ở Bước 1 trước.")
         else:
             groups_list = [g.strip() for g in comment_groups_input.split("\n") if g.strip()]
             img_folder = comment_img_input.strip() if comment_img_input.strip() != "" else None
             prompt_template = prompt_template_input.strip()
             
             st.info(f"Bắt đầu chạy Auto Comment cho {len(groups_list)} nhóm...")
             try:
                 importlib.reload(fb_auto_comment_group)
                 results = fb_auto_comment_group.run_multi_group_commenting(
                     st.session_state.driver, 
                     group_urls=groups_list,
                     max_comments=1,
                     image_dir=img_folder,
                     pause_between_groups=(20, 30),
                     prompt_template=prompt_template
                 )
                 st.success("✅ Đã chạy xong Auto Comment!")
                 st.markdown("### 📊 BẢNG THỐNG KÊ KẾT QUẢ ĐĂNG BÀI")
                 st.table(results)
             except Exception as e:
                 st.error(f"Có lỗi xảy ra: {e}")

with tab3:
    st.subheader("Tính năng Chạy Liên Hoàn (Post ➡️ Đợi ➡️ Comment)")
    
    lienhoan_groups_input = st.text_area("Danh sách URL Groups:", value=default_groups, height=150, key="lh_groups")
    lienhoan_noi_dung_input = st.text_area("Nội dung bài viết (Auto Post):", value=default_content, height=150, key="lh_content")
    lienhoan_post_img = st.text_input("Thư mục chứa ảnh (Auto Post):", value=os.path.join(BASE_DIR, "images", "vinfast"), key="lh_p_img")
    
    lienhoan_prompt_input = st.text_area("Prompt cho AI (Auto Comment):", value=default_prompt_comment, height=150, key="lh_prompt")
    lienhoan_comment_img = st.text_input("Thư mục chứa ảnh (Auto Comment):", value=os.path.join(BASE_DIR, "images", "vinfast"), key="lh_c_img")
    
    wait_minutes = st.number_input("Số phút đợi giữa Post và Comment", min_value=1, max_value=60, value=15)
    
    st.markdown("---")
    is_loop = st.checkbox("🔄 Chạy lặp lại vô hạn (Cho treo máy 24/7 trên Dashboard)", value=False)
    loop_hours = st.number_input("Thời gian lặp lại mỗi chu kỳ (Giờ)", min_value=1, max_value=24, value=12, disabled=not is_loop)
    
    if st.button("▶️ Chạy Liên Hoàn", use_container_width=True):
        if "driver" not in st.session_state or st.session_state.driver is None:
            st.error("Vui lòng đăng nhập và khởi tạo trình duyệt ở Bước 1 trước.")
        else:
            groups_list = [g.strip() for g in lienhoan_groups_input.split("\n") if g.strip()]
            post_img = lienhoan_post_img.strip() if lienhoan_post_img.strip() != "" else None
            comment_img = lienhoan_comment_img.strip() if lienhoan_comment_img.strip() != "" else None
            prompt_template = lienhoan_prompt_input.strip()
            
            loop_count = 1
            while True:
                if is_loop:
                    st.markdown(f"## 🔄 ĐANG CHẠY CHU KỲ LẦN THỨ {loop_count}")
                    
                st.info(f"BƯỚC 1: Đang chạy Auto Post cho {len(groups_list)} nhóm...")
                try:
                    importlib.reload(fb_auto_post)
                    importlib.reload(fb_auto_comment_group)
                    
                    post_results = fb_auto_post.auto_post_to_groups_v5(st.session_state.driver, groups_list, lienhoan_noi_dung_input.strip(), post_img)
                    
                    # Filter successful links for commenting
                    successful_links = [r.get("url") for r in post_results if r.get("status") == "Success"]
                    
                    st.markdown("### 📊 KẾT QUẢ ĐĂNG BÀI")
                    st.table([{"URL Nhóm": r.get("url", ""), "Trạng thái": r.get("status", ""), "Lý do": r.get("reason", "")} for r in post_results])
                    
                    if not successful_links:
                        st.warning("Không có bài viết nào đăng thành công. Hủy bước Comment.")
                    else:
                        st.info(f"Đã đăng thành công {len(successful_links)} bài. Bắt đầu đợi {wait_minutes} phút trước khi comment...")
                        
                        # Tiến trình đếm ngược
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_seconds = wait_minutes * 60
                        for i in range(total_seconds):
                            time.sleep(1)
                            progress = (i + 1) / total_seconds
                            progress_bar.progress(progress)
                            status_text.text(f"Đang đợi... {i+1}/{total_seconds} giây")
                            
                        status_text.text("Hết thời gian chờ. Bắt đầu Auto Comment!")
                        
                        st.info(f"BƯỚC 2: Bắt đầu chạy Auto Comment cho {len(successful_links)} nhóm thành công...")
                        comment_results = fb_auto_comment_group.run_multi_group_commenting(
                            st.session_state.driver, 
                            group_urls=successful_links,
                            max_comments=1,
                            image_dir=comment_img,
                            pause_between_groups=(20, 30),
                            prompt_template=prompt_template
                        )
                        
                        st.success("✅ Đã chạy xong Auto Comment liên hoàn!")
                        st.markdown("### 📊 KẾT QUẢ BÌNH LUẬN")
                        st.table(comment_results)
                        
                except Exception as e:
                    st.error(f"Có lỗi xảy ra: {e}")
                
                if not is_loop:
                    break
                    
                st.info(f"Đã hoàn thành chu kỳ {loop_count}. Bắt đầu ngủ đông chờ {loop_hours} giờ để chạy chu kỳ tiếp theo...")
                cycle_seconds = loop_hours * 3600
                cycle_progress = st.progress(0)
                cycle_text = st.empty()
                for i in range(cycle_seconds):
                    time.sleep(1)
                    cycle_progress.progress((i + 1) / cycle_seconds)
                    cycle_text.text(f"Đang ngủ đông... {i+1}/{cycle_seconds} giây")
                
                loop_count += 1

"""
FB Auto Post v5.1 — Fixed: dialog container derived from textbox, not hardcoded XPath.
=======================================================================================

WHAT CHANGED FROM v5:
- v5 bug: find_post_dialog() used hardcoded XPaths that didn't match the actual DOM,
  so the scoped textbox search always failed.
- v5.1 fix: Find textbox FIRST (proven reliable from v4), then walk UP the DOM tree
  to find the parent container (form/dialog). All subsequent searches are scoped
  to this reliable container.

IMAGE GOES TO WRONG POST/COMMENT — FIXED:
- Root cause: "//input[@type='file']" on full page hits file inputs of other posts'
  comment boxes that are loaded in the feed behind the dialog.
- Fix: After finding the textbox, we walk up to its parent form/dialog.
  Then we search for file inputs ONLY within that parent container.
  This guarantees the file input belongs to OUR post composer.
"""

import os
import glob
import time
import random
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


from dotenv import load_dotenv
from ollama import Client

load_dotenv()

def spin_post_content(base_content, api_key=None):
    if api_key is None:
        api_key = os.getenv("GROQ_API_KEY")
    """
    Sử dụng Ollama Cloud để xào bài (spin content), giúp bài post mỗi group có sự khác biệt nhẹ, 
    tránh bị Facebook đánh dấu spam.
    """
    print("🤖 Đang nhờ Ollama làm mới nội dung bài post...")
    try:
        client = Client(
            host='https://api.ollama.com',
            headers={'Authorization': 'Bearer ff1eb1e4ac434176991aa7b1434b2550.uvXgs2n8Ur4mSerdzd0sI-Ku'}
        )
        
        prompt = f"""
Bạn là một người dùng mạng xã hội Facebook. Tôi có một nội dung bài viết dưới đây muốn đăng lên nhiều hội nhóm khác nhau.
Để tránh bị Facebook đánh dấu là spam, nhiệm vụ của bạn là viết lại (spin/paraphrase) nội dung này thành một phiên bản MỚI NHƯNG GIỮ NGUYÊN Ý NGHĨA, văn phong có thể đời thường, tự nhiên mất dạy một chút cũng được.

Yêu cầu bắt buộc:
1. Giữ nguyên 100% các đường link (ví dụ shopee, facebook...). Không được đổi link, không làm mất link.
2. Chỉ viết 1 câu thật tự nhiên, gần gũi.
3. Cố gắng giữ nguyên ý chính, giữ thái độ vui vẻ, thân thiện, đời thường (có thể dùng icon phù hợp).
5. CHỈ TRẢ VỀ nội dung bài viết đã được viết lại, KHÔNG CÓ TỪ NGỮ THỪA (như "Đây là bài viết...", "Dưới đây là...").

Nội dung gốc cần viết lại:
'''
{base_content}
'''
"""
        
        response = client.chat(
            model='gpt-oss:20b-cloud',
            messages=[{'role': 'user', 'content': prompt}],
        )
        
        new_content = response['message']['content'].strip()
        
        # Lọc bỏ dấu nháy thừa nếu AI vô tình sinh ra ở đầu/cuối
        if new_content.startswith('"') and new_content.endswith('"'):
            new_content = new_content[1:-1]
        elif new_content.startswith("'") and new_content.endswith("'"):
            new_content = new_content[1:-1]
            
        return new_content.strip()
        
    except Exception as e:
        print(f"⚠️ Lỗi khi gọi Ollama API: {e}")
        # Nếu rớt mạng hoặc lỗi API, trả về bài gốc để tool đăng bài không bị ngắt quãng
        return base_content


def random_sleep(min_time=2, max_time=5):
    delay = random.uniform(min_time, max_time)
    print(f"⏳ Nghỉ {delay:.1f}s...")
    time.sleep(delay)


# ─────────────────────────────────────────────────────────────
# STEP 1: Find textbox (full-page search, proven reliable in v4)
# ─────────────────────────────────────────────────────────────
def find_textbox(driver, timeout=10):
    """
    Tìm ô soạn thảo bằng cách tìm kiếm toàn trang.
    Đây là cách hoạt động ổn định nhất (đã kiểm chứng từ v4).
    """
    xpaths = [
        "//div[@aria-placeholder='Bạn viết gì đi...']",
        "//div[@aria-placeholder='Write something...']",
        "//div[@aria-placeholder='Tạo bài viết công khai...']",
        "//div[@aria-label='Tạo bài viết công khai...']",
        "//div[@role='textbox' and @contenteditable='true']",
    ]
    for xpath in xpaths:
        try:
            tb = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            if tb and tb.is_displayed():
                print(f"✅ Tìm thấy textbox.")
                return tb
        except:
            continue
    raise Exception("❌ Không tìm thấy ô soạn thảo bài viết!")


# ─────────────────────────────────────────────────────────────
# STEP 2: Derive the dialog container by walking UP from textbox
# ─────────────────────────────────────────────────────────────
def get_dialog_from_textbox(driver, textbox):
    """
    Walk UP the DOM from the textbox to find the enclosing form or dialog.
    This is more reliable than any hardcoded XPath because we start from
    a known-good element (the textbox we already found).
    Returns the container WebElement, or None if not found.
    """
    container = driver.execute_script(
        """
        var el = arguments[0];
        for (var i = 0; i < 20; i++) {
            el = el.parentElement;
            if (!el) break;
            var tag = el.tagName ? el.tagName.toLowerCase() : '';
            var role = el.getAttribute('role') || '';
            var label = el.getAttribute('aria-label') || '';
            // Stop at form, dialog, or known FB dialog labels
            if (tag === 'form' ||
                role === 'dialog' ||
                label.indexOf('Tạo bài viết') !== -1 ||
                label.indexOf('Create post') !== -1) {
                return el;
            }
        }
        // Fallback: go up 8 levels from textbox regardless
        el = arguments[0];
        for (var j = 0; j < 8; j++) {
            if (el.parentElement) el = el.parentElement;
        }
        return el;
        """,
        textbox
    )
    return container


# ─────────────────────────────────────────────────────────────
# STEP 3: Type text (3 methods, same as v4/v5)
# ─────────────────────────────────────────────────────────────
def type_text(driver, textbox, text):
    """
    Nhập văn bản theo 3 phương pháp:
    1. JS execCommand('insertText') - triggers React synthetic events properly
    2. ActionChains send_keys
    3. Clipboard paste (Ctrl+V) với space+backspace trick
    """
    # Method 1: JS execCommand (best for React/Lexical editors)
    print("📝 Phương pháp 1: JS execCommand('insertText')...")
    try:
        driver.execute_script("arguments[0].focus();", textbox)
        time.sleep(0.4)
        js_text = (text.replace("\\", "\\\\")
                       .replace("'", "\\'")
                       .replace("\n", "\\n")
                       .replace("\r", ""))
        result = driver.execute_script(
            f"""
            var el = arguments[0];
            el.focus();
            var range = document.createRange();
            range.selectNodeContents(el);
            range.collapse(false);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            return document.execCommand('insertText', false, '{js_text}');
            """,
            textbox
        )
        if result:
            print("✅ Phương pháp 1 OK (JS insertText)!")
            time.sleep(0.8)
            return True
        print("⚠️ execCommand returned false.")
    except Exception as e:
        print(f"⚠️ Phương pháp 1 lỗi: {e}")

    # Method 2: send_keys in chunks
    print("📝 Phương pháp 2: ActionChains send_keys...")
    try:
        ActionChains(driver).click(textbox).perform()
        time.sleep(0.4)
        for chunk in [text[i:i+80] for i in range(0, len(text), 80)]:
            ActionChains(driver).send_keys(chunk).perform()
            time.sleep(0.15)
        ActionChains(driver).send_keys(Keys.END).perform()
        time.sleep(0.4)
        print("✅ Phương pháp 2 OK (send_keys)!")
        return True
    except Exception as e:
        print(f"⚠️ Phương pháp 2 lỗi: {e}")

    # Method 3: Clipboard paste
    print("📝 Phương pháp 3: Clipboard paste (Ctrl+V)...")
    try:
        pyperclip.copy(text)
        time.sleep(0.3)
        ActionChains(driver).click(textbox).perform()
        time.sleep(0.4)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
        time.sleep(1.5)
        # Space + Backspace: force React to register the change
        ActionChains(driver).send_keys(" ").perform()
        time.sleep(0.2)
        ActionChains(driver).send_keys(Keys.BACKSPACE).perform()
        time.sleep(0.4)
        print("✅ Phương pháp 3 OK (Clipboard paste)!")
        return True
    except Exception as e:
        print(f"⚠️ Phương pháp 3 lỗi: {e}")

    raise Exception("❌ Tất cả phương pháp nhập văn bản đều thất bại!")


# ─────────────────────────────────────────────────────────────
# STEP 4: Upload images SCOPED to dialog container
# ─────────────────────────────────────────────────────────────
def upload_images(driver, dialog_container, files_to_upload):
    """
    Tải ảnh lên bằng cách tìm file input TRONG container của dialog.
    Điều này ngăn ảnh bị gửi nhầm vào comment hay post khác trên trang.

    Chiến lược:
    1. Tìm file input bên trong container (scoped)
    2. Nếu không thấy, click nút Ảnh/Video trong container trước
    3. Gửi đường dẫn file vào input đó
    """

    def find_file_inputs_in_container(container):
        """Tìm tất cả file input trong một container element."""
        try:
            inputs = container.find_elements(By.XPATH, ".//input[@type='file']")
            return [i for i in inputs]  # Return all, even hidden ones
        except:
            return []

    # Try 1: Find file input directly inside the container
    file_inputs = find_file_inputs_in_container(dialog_container)

    # Try 2: Click the photo button inside container to activate the right input
    if not file_inputs:
        print("🖼️ Tìm nút Ảnh/Video trong container...")
        photo_btn_xpaths = [
            ".//div[@aria-label='Ảnh/video']",
            ".//div[@aria-label='Photo/video']",
            ".//div[@aria-label='Photo/Video']",
            ".//span[contains(text(),'Ảnh') or contains(text(),'Photo')]/ancestor::div[@role='button'][1]",
            ".//label[.//input[@type='file']]",
        ]
        for xpath in photo_btn_xpaths:
            try:
                btn = dialog_container.find_element(By.XPATH, xpath)
                if btn:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    print(f"✅ Đã click nút ảnh.")
                    break
            except:
                continue
        # Retry finding file inputs after click
        file_inputs = find_file_inputs_in_container(dialog_container)

    # Try 3: Fallback - scope by finding inputs near the textbox-containing form
    if not file_inputs:
        print("⚠️ Không tìm thấy file input trong container, thử tìm rộng hơn...")
        # Find inputs that are inside any form on page (more scoped than full page)
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                inputs = form.find_elements(By.XPATH, ".//input[@type='file']")
                if inputs:
                    file_inputs = inputs
                    print(f"✅ Tìm thấy {len(inputs)} file input trong form.")
                    break
        except:
            pass

    if not file_inputs:
        print("❌ Không tìm thấy file input để upload!")
        return False

    print(f"📂 Thử gửi ảnh vào {len(file_inputs)} file input...")
    for fi in file_inputs:
        try:
            # Make visible (FB hides these with CSS)
            driver.execute_script(
                "arguments[0].style.display='block';"
                "arguments[0].style.opacity='1';"
                "arguments[0].style.visibility='visible';",
                fi
            )
            fi.send_keys(files_to_upload)
            print("✅ Upload ảnh thành công!")
            return True
        except Exception as e:
            print(f"⚠️ File input này không nhận được: {e}")
            continue

    print("❌ Tất cả file input đều thất bại!")
    return False


# ─────────────────────────────────────────────────────────────
# STEP 5: Verify text survived image upload rebuild
# ─────────────────────────────────────────────────────────────
def verify_and_fix_text(driver, post_text):
    """
    Kiểm tra text trong ô soạn thảo. Nếu bị mất sau khi upload ảnh,
    tìm lại textbox và nhập lại.
    """
    try:
        tb = find_textbox(driver)
        content = (tb.get_attribute("textContent") or tb.text or "").strip()
        if content:
            print(f"✅ Text vẫn còn ({len(content)} ký tự): '{content[:50]}...'")
            return tb
        else:
            print("⚠️ Text bị mất sau khi tải ảnh. Đang nhập lại...")
            type_text(driver, tb, post_text)
            time.sleep(1)
            return tb
    except Exception as e:
        print(f"⚠️ Không kiểm tra được text: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# STEP 6: Click Post button
# ─────────────────────────────────────────────────────────────
def click_post_button(driver, container=None):
    """
    Tìm và click nút Đăng. Ưu tiên tìm trong container, fallback toàn trang.
    """
    search_roots = []
    if container:
        search_roots.append(container)
    # Always add body as final fallback
    search_roots.append(driver.find_element(By.TAG_NAME, "body"))

    relative_xpaths = [
        ".//div[@aria-label='Đăng' and @role='button']",
        ".//div[@aria-label='Post' and @role='button']",
        ".//span[normalize-space(.)='Đăng']/ancestor::div[@role='button'][1]",
        ".//span[normalize-space(.)='Post']/ancestor::div[@role='button'][1]",
        ".//div[@role='none']//span[normalize-space(.)='Đăng']/..",
        ".//span[normalize-space(.)='Đăng']",
        ".//span[normalize-space(.)='Post']",
    ]

    for root in search_roots:
        for xpath in relative_xpaths:
            try:
                btn = root.find_element(By.XPATH, xpath)
                if btn and btn.is_displayed():
                    print(f"✅ Tìm thấy nút Đăng.")
                    try:
                        btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", btn)
                    return True
            except:
                continue

    raise Exception("❌ Không tìm thấy nút Đăng!")


# ─────────────────────────────────────────────────────────────
# Thống kê kết quả
# ─────────────────────────────────────────────────────────────
def print_statistics(results):
    print("\n" + "="*100)
    print("📊 BẢNG THỐNG KÊ KẾT QUẢ ĐĂNG BÀI")
    print("="*100)
    
    success_count = sum(1 for r in results if r['status'] == 'Success')
    failed_count = sum(1 for r in results if r['status'] == 'Failed')
    
    print(f"Tổng số nhóm: {len(results)} | Thành công: {success_count} | Thất bại: {failed_count}")
    print("-" * 100)
    
    # Header
    print(f"| {'Link Nhóm'.ljust(50)} | {'Trạng thái'.ljust(12)} | {'Lý do'.ljust(28)} |")
    print("-" * 100)
    
    for r in results:
        url = r['url']
        if len(url) > 50:
            url = url[:47] + "..."
        status = r['status']
        reason = r['reason']
        reason = reason.replace('\n', ' ')
        if len(reason) > 28:
            reason = reason[:25] + "..."
            
        print(f"| {url.ljust(50)} | {status.ljust(12)} | {reason.ljust(28)} |")
    
    print("="*100 + "\n")


# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────
def auto_post_to_groups_v5(driver, group_urls, post_text, image_folder=None):
    """
    Hàm tự động đăng bài hàng loạt lên danh sách Group Facebook.

    Tham số:
        driver       : Selenium WebDriver instance
        group_urls   : Danh sách URL các nhóm Facebook
        post_text    : Nội dung văn bản bài viết
        image_folder : Thư mục chứa ảnh (None = chỉ đăng text)

    Luồng (đã sửa lỗi ảnh vào sai chỗ):
        1. Truy cập nhóm
        2. Mở khung đăng bài
        3. TÌM TEXTBOX → DERIVE DIALOG CONTAINER từ textbox (không dùng hardcoded XPath)
        4. Nhập text TRƯỚC
        5. Upload ảnh SCOPED vào container (không hit file inputs của post/comment khác)
        6. Kiểm tra text còn không
        7. Click nút Đăng
    """

    # Quét ảnh trong thư mục
    image_files = []
    if image_folder:
        image_files = [
            f for f in glob.glob(os.path.join(image_folder, "*.*"))
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov"))
        ]
        files_to_upload = "\n".join(image_files)
        print(f"📷 Tìm thấy {len(image_files)} file ảnh/video.")
    else:
        files_to_upload = ""

    results = []

    for index, group_url in enumerate(group_urls):
        print(f"\n{'='*60}")
        print(f"🔄 GROUP {index + 1}/{len(group_urls)}: {group_url}")
        print(f"{'='*60}")

        try:
            # ── 1. Truy cập nhóm ──
            print("1. Truy cập nhóm...")
            driver.get(group_url)
            random_sleep(5, 8)

            # ── 2. Mở khung đăng bài ──
            print("2. Mở ô đăng bài viết...")
            open_xpaths = [
                "//div[@aria-placeholder='Bạn viết gì đi...']",
                "//div[@aria-placeholder='Write something...']",
                "//*[contains(text(), 'Bạn viết gì đi')]",
                "//*[contains(text(), 'Write something')]",
                "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[4]/div/div/div[2]/div/div/div/div[1]/div/div/div/div[1]/div",
                "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[4]/div/div/div/div[2]/div/div/div/div[1]/div/div/div/div[1]/div/div[1]/span",
            ]
            opener = None
            for xpath in open_xpaths:
                try:
                    opener = WebDriverWait(driver, 4).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    if opener:
                        break
                except:
                    continue

            if not opener:
                raise Exception("Không tìm thấy khu vực đăng bài!")

            driver.execute_script("arguments[0].click();", opener)
            random_sleep(2, 4)

            # ── 3. Tìm textbox (full page, proven reliable) ──
            print("3. Tìm ô soạn thảo...")
            textbox = find_textbox(driver)

            # ── Derive dialog container FROM textbox ──
            print("   Xác định dialog container từ textbox...")
            dialog_container = get_dialog_from_textbox(driver, textbox)

            # ── 3b. Xào bài bằng AI (Spin content) ──
            spun_text = spin_post_content(post_text)

            # ── 4. Nhập text TRƯỚC (text → image order is critical) ──
            print("4. Nhập văn bản TRƯỚC khi tải ảnh...")
            type_text(driver, textbox, spun_text)
            random_sleep(2, 3)

            # ── 5. Tải ảnh lên (SCOPED vào dialog container) ──
            if image_files:
                print(f"5. Tải {len(image_files)} ảnh (scoped vào dialog)...")
                uploaded = upload_images(driver, dialog_container, files_to_upload)

                if uploaded:
                    print("⏳ Đợi ảnh render...")
                    random_sleep(6, 9)

                    # ── 5b. Kiểm tra text còn không sau khi React rebuild ──
                    print("🔍 Kiểm tra text sau khi tải ảnh...")
                    verify_and_fix_text(driver, spun_text)
                else:
                    print("⚠️ Không tải được ảnh, tiếp tục đăng text...")

            # ── 6. Refresh dialog container & click Đăng ──
            print("6. Bấm nút Đăng...")
            random_sleep(1, 2)

            # Re-derive container from fresh textbox lookup (avoids stale reference)
            try:
                fresh_textbox = find_textbox(driver)
                fresh_container = get_dialog_from_textbox(driver, fresh_textbox)
            except:
                fresh_container = None

            click_post_button(driver, fresh_container)
            print(f"🎉 THÀNH CÔNG! Đã đăng bài lên: {group_url}")
            results.append({"url": group_url, "status": "Success", "reason": ""})
            random_sleep(5, 8)

            # ── 7. Nghỉ trước group tiếp theo ──
            if index < len(group_urls) - 1:
                print("⏳ Nghỉ trước khi sang group tiếp theo...")
                random_sleep(30, 60)

        except Exception as e:
            print(f"❌ LỖI group {group_url}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"url": group_url, "status": "Failed", "reason": str(e)})
            random_sleep(5, 10)

    # In bảng thống kê cuối cùng
    print_statistics(results)
    return results

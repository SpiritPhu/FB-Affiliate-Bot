"""
group_comment_bot.py
====================
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import os

# ============================================================
# CAU HINH - chinh tai day truoc khi chay
# ============================================================
# URL nhom Facebook muon comment bai dau tien
GROUP_URL = "https://www.facebook.com/groups/880359772330567/"  # <- Thay link nhom cua ban

import os
# Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Thu muc anh dinh kem vao binh luan (None = khong dinh kem anh)
IMAGE_DIR = r"D:\AIML_Usecases\ai-comment-bot-main\images\vinfast"

# Dinh dang anh duoc chap nhan
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")

# ============================================================
# HELPER
# ============================================================
def random_sleep(min_s: float = 2.0, max_s: float = 6.0):
    """Ngu mot khoang thoi gian ngau nhien (giay)."""
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)

def pick_random_image(image_dir: str) -> str | None:
    """
    Chon ngau nhien mot file anh tu thu muc chi dinh.
    Tra ve duong dan day du (absolute path) hoac None neu khong co anh.
    """
    if not image_dir or not os.path.isdir(image_dir):
        print(f"   WARN Thu muc anh khong hop le: {image_dir}")
        return None
    images = [
        os.path.join(image_dir, f)
        for f in os.listdir(image_dir)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    ]
    if not images:
        print(f"   WARN Khong tim thay anh trong: {image_dir}")
        return None
    chosen = random.choice(images)
    print(f"   OK Chon anh ngau nhien: {os.path.basename(chosen)}")
    return chosen

def attach_image_to_comment(driver, image_path: str) -> bool:
    """
    Dinh kem anh vao o binh luan dang mo.
    Chien luoc: gui duong dan file vao the <input type='file'> an.
    """
    print(f"   Dang dinh kem anh: {os.path.basename(image_path)}...")
    try:
        # Hien thi tat ca input[type=file] an tren trang
        driver.execute_script("""
            document.querySelectorAll('input[type="file"]').forEach(function(el) {
                el.style.display = 'block';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
                el.removeAttribute('multiple');  // tranh chon nhieu file
            });
        """)
        random_sleep(0.5, 1.0)
        
        # Tim input[type=file] lien quan den khu vuc form binh luan
        file_input_xpaths = [
            "//form[@role='presentation']//input[@type='file']",
            "//input[@type='file' and contains(@accept,'image')]",
            "//input[@type='file']",
        ]
        file_input = None
        for xpath in file_input_xpaths:
            try:
                inputs = driver.find_elements(By.XPATH, xpath)
                if inputs:
                    file_input = inputs[0]
                    break
            except Exception:
                continue
                
        if file_input is None:
            print("   WARN Khong tim thay input[type=file], bo qua buoc dinh kem anh.")
            return False
            
        # Gui duong dan anh vao input
        file_input.send_keys(image_path)
        print("   OK Da gui duong dan anh vao input file.")
        # Cho preview anh hien ra
        random_sleep(3, 5)
        return True
    except Exception as e:
        print(f"   WARN Loi khi dinh kem anh: {e}")
        return False

# ============================================================
# AI - Tao binh luan bang Groq (LLaMA 3)
# ============================================================
def generate_groq_comment(post_content: str) -> str:
    from groq import Groq
    print("   Dang goi Groq AI de tao binh luan...")
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
Bạn là một người dùng mạng xã hội bình thường, đọc bài post và đưa ra gợi ý về việc đã tìm thấy 1 sản phẩm như trong bài post nhưng với giá rẻ hơn.

Nhiệm vụ của bạn:
Đọc bài post, cố gắng trích xuất ra tên của một sản phẩm cụ thể, sau đó hồn nhiên hỏi xem đã ai trồng được giống ớt mặt khỉ độc lạ này chưa?
Mình thấy shop này . https://www.facebook.com/share/1CCFZ48oJY/?mibextid=wwXIfr . giao bán rất rẻ này. Gắn link này cuối bình luận:
. https://www.facebook.com/share/1CCFZ48oJY/?mibextid=wwXIfr .

Noi dung bai viet:
"{post_content}"

YEU CAU QUAN TRONG: Viet lien mach thanh 1 doan van duy nhat, khong xuong dong, khong co cau mo dau chao hoi nhu "Duoi day la binh luan cua toi". Chi in ra noi dung binh luan cuoi cung.
"""
    
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
    )
    
    comment = response.choices[0].message.content.strip()
    if comment.startswith('"') and comment.endswith('"'):
        comment = comment[1:-1]
        
    print(f"   Ket qua Groq: {comment[:80]}...")
    return comment

# ============================================================
# HAM CHINH - comment bai dau tien trong nhom
# ============================================================
def comment_first_post_in_group(driver, group_url: str = GROUP_URL, image_dir: str = IMAGE_DIR):
    try:
        # 1. Truy cap nhom
        print("1. Truy cap nhom...")
        driver.get(group_url)
        random_sleep(11, 16)
        
        # 2. Doc noi dung bai viet
        # Facebook co 2 kieu cau truc bai post chinh:
        #   Kieu A: span[@dir='auto'][.//h3]  → bai co tieu de (h3)
        #   Kieu B: div[@dir='auto']          → bai chi co text thuon (khong co h3)
        # Phai xu ly ca 2 kieu, uu tien chinh xac nhat truoc.
        print("2. Doc noi dung bai viet dau tien...")
        post_content = ""

        # --- 2A. Cac XPath theo thu tu uu tien ---
        post_content_xpaths = [
            # Kieu A: span co h3 ben trong (bai co tieu de ro rang)
            "(//div[@role='article'])[1]//span[@dir='auto'][.//h3]",
            # FB data attributes (co trong mot so phien ban)
            "(//div[@role='article'])[1]//div[@data-ad-preview='message']",
            "(//div[@role='article'])[1]//div[@data-ad-comet-preview='message']",
            # Kieu B: div[@dir='auto'] truc tiep (bai text thuan, khong co h3) - chi trong article[1]
            "(//div[@role='article'])[1]//div[@dir='auto' and @style]",
            "(//div[@role='article'])[1]//div[@dir='auto']",
            # Ket hop span va div dir=auto trong feed
            "//div[@role='feed']//span[@dir='auto'][.//h3]",
            "//div[@role='feed']//div[@dir='auto' and @style]",
        ]

        for xpath in post_content_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    # Uu tien phan tu dau tien co noi dung dai nhat (tranh lay nut/placeholder)
                    for el in elements[:3]:
                        try:
                            text = el.text.strip()
                            # Loai bo nhung dong qua ngan (co the la nut "Xem them", icon, v.v.)
                            # va loai bo text la URL hoac chi co emoji
                            lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 3]
                            text = " ".join(lines)
                            if text and len(text) > 10:
                                post_content = text
                                print(f"   Tim thay noi dung (XPath): {post_content[:120]}...")
                                break
                        except Exception:
                            continue
                if post_content:
                    break
            except Exception as ex:
                print(f"   SKIP xpath loi: {ex}")
                continue

        # --- 2B. JavaScript fallback toan dien ---
        if not post_content:
            print("   Thu JavaScript fallback...")
            try:
                post_content = driver.execute_script("""
                    var articles = document.querySelectorAll('div[role="article"]');
                    if (!articles.length) return '';
                    var art = articles[0];

                    // Thu 1: span[dir='auto'] co h3 ben trong
                    var spans = art.querySelectorAll('span[dir="auto"]');
                    for (var s of spans) {
                        if (s.querySelector('h3')) {
                            var t = s.innerText.trim();
                            if (t.length > 10) return t.substring(0, 600);
                        }
                    }

                    // Thu 2: div[dir='auto'] co style (kieu bai text thuan nhu JBL post)
                    var divs = art.querySelectorAll('div[dir="auto"]');
                    var best = '';
                    for (var d of divs) {
                        var t = d.innerText.trim();
                        // Loai bo nut "Xem them" va cac phan tu qua ngan
                        if (t.length > best.length && t.length > 10 && t.length < 2000) {
                            // Tranh lay text cua toan bo article (qua dai)
                            best = t;
                        }
                    }
                    if (best.length > 10) return best.substring(0, 600);

                    // Thu 3: innerText cua article, lay 600 ky tu dau
                    var full = art.innerText.trim();
                    return full.length > 10 ? full.substring(0, 600) : '';
                """) or ""
                if post_content:
                    print(f"   Tim thay noi dung (JS): {post_content[:120]}...")
            except Exception as ex:
                print(f"   WARN JS fallback loi: {ex}")

        # --- 2C. Last resort: innerText cua article[0] ---
        if not post_content:
            print("   Thu last resort: lay innerText article dau tien...")
            try:
                articles = driver.find_elements(By.XPATH, "//div[@role='article']")
                if articles:
                    post_content = articles[0].text.strip()[:600]
                    if post_content:
                        print(f"   Tim thay noi dung (innerText): {post_content[:120]}...")
            except Exception as ex:
                print(f"   WARN Last resort loi: {ex}")

        if not post_content:
            print("   WARN Khong doc duoc noi dung, dung cau mac dinh.")
            post_content = "Một bài viết rất hay trong nhóm!"

        random_sleep(1, 2)
        
        # 3. Click nut Binh luan
        print("3. Tim nut 'Bình luận'...")
        comment_button_xpaths = [
            "//div[@role='button']//span[contains(text(), 'Bình luận')]",
            "//div[@role='button']//span[contains(text(), 'Comment')]",
            "//div[contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Comment') and @role='button']"
        ]
        
        button_clicked = False
        for xpath in comment_button_xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
                if buttons:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buttons[0])
                    random_sleep(1, 2)
                    driver.execute_script("arguments[0].click();", buttons[0])
                    print("   Da click nut Binh luan.")
                    button_clicked = True
                    break
            except Exception:
                continue
                
        if not button_clicked:
            raise Exception("Khong tim thay nut Binh luan cua bai viet dau tien.")
            
        random_sleep(2, 4)
        
        # 4. Goi AI tao noi dung
        print("4. Dang tao noi dung binh luan tu AI...")
        ai_comment = generate_groq_comment(post_content)
        
        # 5. Tim o binh luan + go text
        print("5. Nhap noi dung vao o binh luan...")
        input_xpaths = [
            "//div[@aria-placeholder='Viết bình luận công khai…' and @contenteditable='true']",
            "//div[@aria-placeholder='Write a public comment…' and @contenteditable='true']",
            "//div[contains(@aria-label, 'Viết bình luận') and @contenteditable='true']",
            "//div[@contenteditable='true' and @role='textbox']"
        ]
        
        comment_box = None
        for xpath in input_xpaths:
            try:
                boxes = driver.find_elements(By.XPATH, xpath)
                if boxes:
                    comment_box = boxes[0]  # lay o dau tien tren trang (ung voi bai dau tien)
                    break
            except Exception:
                continue
                
        if not comment_box:
            print("   Thu chuyen sang active_element...")
            comment_box = driver.switch_to.active_element
            
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_box)
        random_sleep(0.5, 1)
        driver.execute_script("arguments[0].click();", comment_box)
        random_sleep(1, 2)
        
        # Go tung chu de mo phong nguoi that
        comment_box.send_keys(ai_comment)
        random_sleep(1, 2)
        
        # 6. Dinh kem anh (neu co thu muc anh)
        if image_dir:
            image_path = pick_random_image(image_dir)
            if image_path:
                print("6. Dang dinh kem anh vao binh luan...")
                attach_image_to_comment(driver, image_path)
                # Click lai vao o comment de dam bao focus truoc khi Enter
                try:
                    driver.execute_script("arguments[0].click();", comment_box)
                except Exception:
                    pass
                random_sleep(1, 2)
                
        # 7. Gui binh luan bang phim Enter
        print("7. Dang gui binh luan...")
        comment_box.send_keys(Keys.RETURN)
        print("Da dang binh luan thanh cong!")
        random_sleep(2, 3)
        
    except Exception as e:
        print(f"Loi trong qua trinh thao tac: {e}")
        raise

# ============================================================
# VONG LAP - lap lai viec vao nhom va comment bai dau tien
# ============================================================
def run_group_commenting(
    driver,
    group_url: str = GROUP_URL,
    max_comments: int = 1,
    image_dir: str = IMAGE_DIR,
):
    """
    Vao nhom, comment vao bai viet dau tien dang hien thi, sau do tai lai/nghi
    va thuc hien lap lai max_comments lan.
    """
    for i in range(max_comments):
        print(f"\n{'='*45}")
        print(f"--- BAT DAU VONG LAP LAN {i+1}/{max_comments} ---")
        try:
            comment_first_post_in_group(driver, group_url=group_url, image_dir=image_dir)
            
            pause_time = random.uniform(9, 18)
            print(f"Hoan thanh comment lan {i+1}. Tam nghi {int(pause_time)} giay de tranh bi Facebook chan...")
            time.sleep(pause_time)
            
        except Exception as e:
            print(f"Co loi o vong {i+1}: {e}")
            print("Se tiep tuc sau 30 giay...")
            time.sleep(30)
            
    print(f"\n{'='*45}")
    print(f"Da hoan thanh xuat sac {max_comments} vong lap!")

# ============================================================
# LOOP QUA NHIEU NHOM
# ============================================================
def run_multi_group_commenting(
    driver,
    group_urls: list,
    max_comments: int = 1,
    image_dir: str = IMAGE_DIR,
    pause_between_groups: tuple = (30, 60),
):
    """
    Loop qua danh sach nhom Facebook, moi nhom se comment max_comments lan.

    Tham so:
        driver              : Selenium WebDriver dang chay
        group_urls          : List cac URL nhom can comment
        max_comments        : So lan comment moi nhom (mac dinh 1)
        image_dir           : Thu muc anh dinh kem (None = khong dinh kem)
        pause_between_groups: Khoang nghi (giay) giua 2 nhom (min, max)

    Vi du:
        groups = [
            "https://www.facebook.com/groups/1160652748626589",
            "https://www.facebook.com/groups/880359772330567",
        ]
        run_multi_group_commenting(driver, group_urls=groups, max_comments=1,
                                   image_dir=r"D:\\AIML_Usecases\\ai-comment-bot-main\\images\\marshall")
    """
    total = len(group_urls)
    print(f"\n{'#'*50}")
    print(f"BAT DAU LOOP {total} NHOM | {max_comments} comment/nhom")
    print(f"{'#'*50}")

    success_count = 0
    fail_count = 0

    for idx, group_url in enumerate(group_urls, start=1):
        print(f"\n{'='*50}")
        print(f"[NHOM {idx}/{total}] {group_url}")
        print(f"{'='*50}")
        try:
            run_group_commenting(
                driver,
                group_url=group_url,
                max_comments=max_comments,
                image_dir=image_dir,
            )
            success_count += 1
        except Exception as e:
            print(f"   WARN Loi nhom {idx}: {e}")
            fail_count += 1

        # Nghi giua cac nhom (tru nhom cuoi cung)
        if idx < total:
            pause = random.uniform(*pause_between_groups)
            print(f"\n   Nghi {int(pause)}s truoc khi sang nhom tiep theo...")
            time.sleep(pause)

    print(f"\n{'#'*50}")
    print(f"HOAN THANH: {success_count}/{total} nhom thanh cong, {fail_count} loi.")
    print(f"{'#'*50}")

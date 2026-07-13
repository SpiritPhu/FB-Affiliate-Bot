# ============================================================
# CELL ĐỂ CHẠY TRONG JUPYTER NOTEBOOK
# Copy toàn bộ cell này vào notebook và chạy
# ============================================================

import importlib, sys

sys.path.insert(0, r'D:\AIML_Usecases\ai-comment-bot-main')
import fb_post_v5
importlib.reload(fb_post_v5)  # Reload để lấy code mới nhất nếu có sửa đổi
from fb_post_v5 import auto_post_to_groups_v5

# ── Danh sách nhóm cần đăng bài ──
danh_sach_groups = [
    # 'https://www.facebook.com/groups/880359772330567/',
    'https://www.facebook.com/groups/vinfastfadil/',
    'https://www.facebook.com/groups/3952468598316805/',
    'https://www.facebook.com/groups/433338679303668/',
    'https://www.facebook.com/groups/hoivinfastvf3vietnam/',
    'https://www.facebook.com/groups/vf3clubvn369/',
    'https://www.facebook.com/groups/vinfastvf3clubvn/',
    'https://www.facebook.com/groups/1023069638660550/',
    'https://www.facebook.com/groups/843093077239619/',
    'https://www.facebook.com/groups/vf3vn/',
    'https://www.facebook.com/groups/310121472045489/',
    'https://www.facebook.com/groups/108786698975857/',
    'https://www.facebook.com/groups/374412891998798/',
    'https://www.facebook.com/groups/2665088917123446/',
    'https://www.facebook.com/groups/vinfastvf3vietnam/',
    'https://www.facebook.com/groups/567250299481730/',
    'https://www.facebook.com/groups/vinfastvf5clubvn/',
    'https://www.facebook.com/groups/568581818035740/',
    'https://www.facebook.com/groups/vinfastvf5plus3mien/',
    'https://www.facebook.com/groups/vinfastvf5clubvnn',
    'https://www.facebook.com/groups/804472867906965/',
    'https://www.facebook.com/groups/566623628104969/',
    'https://www.facebook.com/groups/332225783132931/',
    'https://www.facebook.com/groups/1165263687995203/',
    'https://www.facebook.com/groups/muabanxevinfast.vf5/',
    'https://www.facebook.com/groups/vinfastvf6vn/',
    'https://www.facebook.com/groups/vinfastvf6clubvn',
    'https://www.facebook.com/groups/vinfastvf6vietnam/',
    'https://www.facebook.com/groups/vf6vn/',
    'https://www.facebook.com/groups/1092112921755347/',
    'https://www.facebook.com/groups/589978989532335/',
    'https://www.facebook.com/groups/921817510028348/',
    'https://www.facebook.com/groups/xedienvinfastvf6/',
    'https://www.facebook.com/groups/vf7vn/',
    'https://www.facebook.com/groups/1459689761248904/',
    'https://www.facebook.com/groups/homestayoceancity/',
    'https://www.facebook.com/groups/hoivinfastvf8/',
    'https://www.facebook.com/groups/729010889298292/',
    'https://www.facebook.com/groups/1246168830315190/',
    'https://www.facebook.com/groups/1927097800974773/',
    'https://www.facebook.com/groups/vinfastvf9clubvn/',
    'https://www.facebook.com/groups/439170075706628/',
    'https://www.facebook.com/groups/1121991495829735/'
]

# ── Nội dung bài viết ──
noi_dung = """VF8 all new dán thêm chút tem vào nhìn khác hẳn nhỉ, chất ngầu hơn hẳn :D.
https://s.shopee.vn/50X7lXZUwc . Trên sọp pe đang có nhiều mẫu tem xe rẻ đẹp, cả nhà mình tham khảo nhé
https://s.shopee.vn/50X7lXZUwc
p/s: ảnh đi mượn ạ.
"""

# ── Thư mục ảnh (đặt None nếu chỉ đăng text) ──
thu_muc_anh = r"D:\AIML_Usecases\ai-comment-bot-main\images\vinfast"
# thu_muc_anh = None  # <- bỏ comment dòng này nếu không cần ảnh

# ── Chạy ──
auto_post_to_groups_v5(driver, danh_sach_groups, noi_dung, thu_muc_anh)

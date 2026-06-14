import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Tải key từ file .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("Chưa tìm thấy GEMINI_API_KEY trong file .env. Hãy kiểm tra lại!")

# Khởi tạo Client theo chuẩn SDK genai mới nhất
client = genai.Client(api_key=GOOGLE_API_KEY)

# Sử dụng model gemini-2.5-flash theo chuẩn API mới để ổn định và không kẹt version
MODEL_ID = 'gemini-2.5-flash'

def analyze_sentiment(topic, text_data_list):
    """
    Nhồi toàn bộ dữ liệu cào được vào AI ra kết quả dưới dạng JSON có cấu trúc.
    """
    if not text_data_list:
        return {"error": "Không có dữ liệu đầu vào."}

    # Gom các bình luận thành 1 cục text bự, đánh số thứ tự cho AI dễ đọc
    combined_text = "\n".join([f"{i+1}. {text}" for i, text in enumerate(text_data_list)])
    
    if len(combined_text) > 30000:
        print("[!] Dữ liệu quá lớn, đang cắt bớt để tập trung phân tích các kết quả hot nhất...")
        combined_text = combined_text[:30000]

    prompt = f"""
Bạn là một chuyên gia phân tích dữ liệu tâm lý khách hàng (Customer Sentiment Analyst).
Dưới đây là tập hợp các phản hồi, bài đăng, bình luận cào được từ không gian mạng (Reddit) về chủ đề/sản phẩm: "{topic}".

NHIỆM VỤ CỦA BẠN:
1. Đọc kỹ và xác định tỷ lệ % sắc thái của dư luận: Tích cực, Tiêu cực, và Trung lập (tổng phải bằng 100).
2. Tìm ra mấu chốt: 3 điểm người ta khen nhiều nhất và 3 điểm người ta chê/bức xúc nhiều nhất.
3. TRẢ VỀ ĐÚNG ĐỊNH DẠNG JSON dưới đây, KHÔNG kèm thêm markdown, KHÔNG thêm lời giải thích nào khác ngoài JSON:

{{
  "tong_quan": "Tích Cực / Tiêu Cực / Trung Lập / Trái Chiều",
  "phan_tram_tich_cuc": 60,
  "phan_tram_tieu_cuc": 30,
  "phan_tram_trung_lap": 10,
  "top_3_khen": [
    "Lý do khen 1 (Viết bằng tiếng Việt)",
    "Lý do khen 2",
    "Lý do khen 3"
  ],
  "top_3_che": [
    "Lý do chê/vấn đề 1 (Viết bằng tiếng Việt)",
    "Lý do chê/vấn đề 2",
    "Lý do chê/vấn đề 3"
  ],
  "ket_luan_ngan": "Một câu chốt hạ tổng kết tình hình (1-2 dòng)"
}}

--- BẮT ĐẦU DỮ LIỆU ĐẦU VÀO ---
{combined_text}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[*] 🧠 Đang đánh thức AI ({MODEL_ID}) (Lần {attempt+1}/{max_retries})...")
            # Sử dụng SDK genai mới
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2, # Giảm sáng tạo để trả về cấu trúc chuẩn JSON
                )
            )
            
            result_json = json.loads(response.text)
            return result_json
            
        except Exception as e:
            err_msg = str(e)
            # Nếu máy chủ quá tải (503) hoặc quá giới hạn (429), ta tự động chờ và chạy lại
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                print(f"   [!] Máy chủ Google đang kẹt xe (Quá tải). Đang tạm nghỉ 5 giây rồi thử lại...")
                time.sleep(5)
                continue
                
            print(f"[!] ❌ Lỗi lạ khi phân tích AI: {e}")
            return None
            
    print("[!] ❌ Bó tay. Máy chủ Google sập toàn tập hôm nay rồi. Vui lòng quay lại sau.")
    return None

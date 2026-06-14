import sys
from scraper import fetch_market_data
from analyzer import analyze_sentiment

def main():
    print("="*60)
    print("🚀 HỆ THỐNG PHÂN TÍCH TÂM LÝ THỊ TRƯỜNG (DÙNG AI) 🚀")
    print("="*60)
    print()
    
    # 1. Nhập liệu
    topic = input("Nhập sản phẩm/chủ đề bạn muốn soi (VD: Cybertruck, iPhone 15...): ").strip()
    if not topic:
        print("Chưa nhập chủ đề, tự động thoát.")
        return

    # 2. Cào dữ liệu (Bot Thợ Mỏ)
    print(f"\n[BƯỚC 1] BẮT ĐẦU ĐÀO DỮ LIỆU TỪ TIN TỨC & DIỄN ĐÀN (Hacker News + Google News)...")
    data_list = fetch_market_data(topic, limit=50) # Cố lấy 50 bài gần nhất mỗi nguồn
    
    if not data_list:
        print("\n[!] Không múc được dữ liệu nào. Có vẻ từ khóa hiếm quá.")
        return
        
    print(f"Tổng khối lượng text chuẩn bị nhồi vào AI: ~{sum(len(t) for t in data_list):,} ký tự.")
    
    # 3. Phân tích bằng AI (Bot Phân Tích)
    print("\n[BƯỚC 2] TRUYỀN DỮ LIỆU CHO BỘ NÃO MÁY GEMINI...")
    result = analyze_sentiment(topic, data_list)
    
    if not result:
        print("\n[!] Chết dở, lỗi khi đọc tính toán tâm lý :(")
        return
        
    # 4. Trình bày Báo cáo đẹp mắt (Bot Báo Cáo)
    print("\n\n" + "="*60)
    print(f"📊 BẢNG BÁO CÁO CẢM XÚC THỊ TRƯỜNG: {topic.upper()} 📊")
    print("="*60)
    print(f">> THÁI ĐỘ TỔNG QUAN: {str(result.get('tong_quan', 'Không rõ')).upper()}")
    
    # Căn lề số liệu %
    tich_cuc = result.get('phan_tram_tich_cuc', 0)
    tieu_cuc = result.get('phan_tram_tieu_cuc', 0)
    trung_lap = result.get('phan_tram_trung_lap', 0)
    print(f">> TỶ LỆ DƯ LUẬN: Tích cực ({tich_cuc}%) | Tiêu cực ({tieu_cuc}%) | Trung lập ({trung_lap}%)")
    
    print("\n✅ TOP 3 ĐIỂM NGƯỜI TA KHEN NHIỀU NHẤT:")
    for idx, khen in enumerate(result.get('top_3_khen', [])):
        print(f"  {idx+1}. {khen}")
        
    print("\n❌ TOP 3 ĐIỂM NGƯỜI TA BỨC XÚC/CHÊ TRÁCH:")
    for idx, che in enumerate(result.get('top_3_che', [])):
        print(f"  {idx+1}. {che}")
        
    print("\n💡 KẾT LUẬN CỦA CHUYÊN GIA AI:")
    print(f"  {result.get('ket_luan_ngan', '...')}")
    print("="*60)
    print("✨ Hoàn tất báo cáo! ✨")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã hủy chương trình.")

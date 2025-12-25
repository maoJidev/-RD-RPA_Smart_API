import json
import os

OUTPUT_DIR = "output"
INPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_contents.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_contents_filtered.json")

def is_valid_document(doc):
    """
    ตรวจสอบว่าเอกสารมีความถูกต้องหรือไม่
    - เลขที่หนังสือ ต้องไม่เหมือนกับช่องข้อมูลหลักอื่นๆ (ซึ่งแสดงว่าดึงข้อมูลผิดพลาดจากต้นทาง)
    """
    book_no = doc.get("เลขที่หนังสือ", "").strip()
    
    # ถ้าไม่มีเลขที่หนังสือเลย ก็ถือว่าไม่สมบูรณ์
    if not book_no:
        return False
        
    # เช็คว่าเลขที่หนังสือไปซ้ำกับฟิลด์อื่นหรือไม่ (กรณีเว็บแสดงผลผิดพลาด)
    fields_to_check = ["เรื่อง", "ข้อกฎหมาย", "ข้อหารือ", "แนววินิจฉัย"]
    for field in fields_to_check:
        if doc.get(field, "").strip() == book_no:
            return False
            
    return True

def run_filter_documents():
    """
    อ่านไฟล์ JSON และคัดกรองเฉพาะข้อมูลที่สมบูรณ์
    """
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ไม่พบไฟล์ {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered_results = []

    for month_data in data:
        original_docs = month_data.get("documents", [])
        
        # 1. คัดกรองเอกสารรายตัวในแต่ละเดือน
        valid_docs = [doc for doc in original_docs if is_valid_document(doc)]
        
        # 2. ถ้าเดือนนั้นมีเอกสารที่ผ่านการกรองแล้ว ให้เก็บไว้
        if valid_docs:
            # สร้าง copy ของ month_data แต่เปลี่ยน list documents
            new_month_data = month_data.copy()
            new_month_data["documents"] = valid_docs
            new_month_data["total_valid_docs"] = len(valid_docs)
            new_month_data["removed_docs"] = len(original_docs) - len(valid_docs)
            filtered_results.append(new_month_data)
        else:
            print(f"⚠️ ตัดเดือน {month_data.get('year')} {month_data.get('month')} ออกเนื่องจากไม่มีข้อมูลที่สมบูรณ์")

    # บันทึกผลลัพธ์
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 กรองข้อมูลเสร็จสิ้น!")
    print(f"📁 บันทึกลง: {OUTPUT_FILE}")
    print(f"📊 จำนวนเดือนที่เหลือ: {len(filtered_results)} เดือน")

if __name__ == "__main__":
    run_filter_documents()

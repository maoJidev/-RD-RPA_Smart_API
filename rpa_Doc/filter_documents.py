import json
import os

OUTPUT_DIR = "output"
INPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_contents.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_contents_filtered.json")


def is_valid_document(doc):
    """
    ตรวจสอบว่าเอกสารมีความถูกต้องหรือไม่
    - เลขที่หนังสือ ต้องไม่เหมือนกับช่องข้อมูลหลักอื่นๆ
    """
    book_no = doc.get("เลขที่หนังสือ", "").strip()
    
    if not book_no:
        return False
        
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

    # ---------------------------
    # LOG SUMMARY (ตัวนับรวม)
    # ---------------------------
    total_months = len(data)
    total_docs_before = 0
    total_docs_after = 0
    total_docs_removed = 0

    print("\n📊 เริ่มกระบวนการกรองข้อมูลเอกสาร")
    print("=" * 60)

    for month_data in data:
        year = month_data.get("year")
        month = month_data.get("month")

        original_docs = month_data.get("documents", [])
        total_docs_before += len(original_docs)

        # 1. คัดกรองเอกสารรายตัว
        valid_docs = [doc for doc in original_docs if is_valid_document(doc)]

        removed_count = len(original_docs) - len(valid_docs)
        total_docs_after += len(valid_docs)
        total_docs_removed += removed_count

        # LOG รายเดือน
        print(
            f"📅 {year} {month} | "
            f"ทั้งหมด: {len(original_docs)} | "
            f"ผ่าน: {len(valid_docs)} | "
            f"ถูกตัด: {removed_count}"
        )

        # 2. เก็บเฉพาะเดือนที่ยังมีข้อมูล
        if valid_docs:
            new_month_data = month_data.copy()
            new_month_data["documents"] = valid_docs
            new_month_data["total_valid_docs"] = len(valid_docs)
            new_month_data["removed_docs"] = removed_count
            filtered_results.append(new_month_data)
        else:
            print(
                f"⚠️ ตัดเดือน {year} {month} "
                f"ออก (ไม่มีข้อมูลที่สมบูรณ์)"
            )

    # ---------------------------
    # บันทึกไฟล์
    # ---------------------------
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # SUMMARY LOG (สรุปรวม)
    # ---------------------------
    print("\n" + "=" * 60)
    print("🎉 สรุปผลการกรองข้อมูล")
    print("=" * 60)
    print(f"📁 ไฟล์ต้นฉบับ        : {INPUT_FILE}")
    print(f"📁 ไฟล์ผลลัพธ์        : {OUTPUT_FILE}")
    print(f"📆 จำนวนเดือนทั้งหมด  : {total_months}")
    print(f"📆 เดือนที่เหลือ       : {len(filtered_results)}")
    print(f"📄 เอกสารก่อนกรอง     : {total_docs_before}")
    print(f"✅ เอกสารที่ผ่านกรอง   : {total_docs_after}")
    print(f"❌ เอกสารถูกตัดออก     : {total_docs_removed}")
    print("=" * 60)


if __name__ == "__main__":
    run_filter_documents()

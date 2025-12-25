import json, os
from urllib.parse import urljoin
from playwright.sync_api import Page

TH_MONTH_MAP = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
}

def collect_months(page: Page):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "months.json")

    year_file = os.path.join(output_dir, "years.json")
    if not os.path.exists(year_file):
        print(f"❌ ไฟล์ปี {year_file} ไม่พบ")
        return

    with open(year_file, "r", encoding="utf-8") as f:
        years = json.load(f)

    months = []
    seen = set()

    for y in years:
        page.goto(y["url"])

        # รอ submenu เดือนของปีนั้น
        page.wait_for_selector(
            "div.link-list-line div.submenu ul li a[title]"
        )

        month_links = page.locator(
            "div.link-list-line div.submenu ul li a[title]"
        ).all()

        for a in month_links:
            month_name = a.inner_text().strip()
            month_no = TH_MONTH_MAP.get(month_name)

            # ป้องกัน garbage
            if not month_no:
                continue

            href = a.get_attribute("href")
            full_url = urljoin(page.url, href)

            key = (y["year"], month_no)
            if key in seen:
                continue
            seen.add(key)

            months.append({
                "year": y["year"],
                "month": month_name,
                "month_no": month_no,
                "url": full_url
            })

    # sort: ปีใหม่ → เก่า, เดือนใหม่ → เก่า
    months.sort(
        key=lambda x: (int(x["year"]), x["month_no"]),
        reverse=True
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(months, f, ensure_ascii=False, indent=2)

    print(f"✅ บันทึกเดือนทั้งหมด {len(months)} รายการ -> {output_file}")

from robocorp.tasks import task
from robocorp.browser import browser
import json

from src.config.settings import FILE_PATHS
from src.utils.document_filter_by_title import filter_documents_by_keywords
from src.utils.document_summarizer import summarize_documents

from src.scrapers.year_collector import collect_years
from src.scrapers.month_collector import collect_months
from src.scrapers.document_url_collector import run_collect_month_urls
from src.scrapers.document_reader import run_read_document_content
from src.utils.document_filter import run_filter_documents
from src.utils.cleanup import clean_logs


@task
def run_year():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 1: Collect years")
        collect_years(page)


@task
def run_month():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 2: Collect months")
        collect_months(page)


@task
def run_collect_month_urls_task():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 3: Collect document URLs")
        run_collect_month_urls(page)


@task
def run_read_document_content_task():
    with browser() as b:
        page = b.new_page()
        print("[INFO] Stage 4: Read document contents")
        run_read_document_content(page)


@task
def run_filter_documents_task():
    print("[INFO] Stage 5: Filter valid documents")
    run_filter_documents()


@task
def run_filter_documents_by_title_task():
    print("[INFO] Stage 6: Filter documents by title keyword")

    input_file = FILE_PATHS["month_document_contents_filtered"]
    with open(input_file, "r", encoding="utf-8") as f:
        all_documents = json.load(f)

    documents = []
    for month in all_documents:
        for doc in month.get("documents", []):
            documents.append({
                "title": doc.get("เรื่อง", ""),
                "content": doc.get("แนววินิจฉัย", "")
            })

    target_keywords = ["ภาษีมูลค่าเพิ่ม", "อาหารสัตว์"]
    filtered_documents = filter_documents_by_keywords(documents, target_keywords)

    if filtered_documents:
        print(f"[OK] Filtered {len(filtered_documents)} documents")
    else:
        print("[NOT_OK] No documents matched keywords")

    output_file = FILE_PATHS["month_document_urls_filtered"]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_documents, f, ensure_ascii=False, indent=2)

    print(f"[OK] Output saved -> {output_file}")


@task
def run_summarize_filtered_documents_task():
    print("[INFO] Stage 7: Summarize filtered documents")

    input_file = FILE_PATHS["month_document_urls_filtered"]
    with open(input_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    summaries = summarize_documents(documents)

    output_file = FILE_PATHS["month_document_urls_summary"]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"[OK] Summary saved -> {output_file}")


@task
def run_cleanup():
    print("[INFO] Stage 8: Cleanup logs")
    clean_logs()
    print("[OK] Cleanup completed")

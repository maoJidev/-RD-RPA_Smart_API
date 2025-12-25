from robocorp.tasks import task
from robocorp.browser import browser

from year_collector import collect_years
from month_collector import collect_months
from collect_month_document_urls import run_collect_month_urls
from read_document_content import run_read_document_content
from filter_documents import run_filter_documents


@task
def run_year():
    with browser() as b:
        page = b.new_page()
        print("📌 Stage 1: เก็บปี")
        collect_years(page)


@task
def run_month():
    with browser() as b: 
        page = b.new_page()
        print("📌 Stage 2: เก็บเดือน")
        collect_months(page)


@task
def run_collect_month_urls_task():
    with browser() as b:
        page = b.new_page()
        print("📌 Stage 3: เก็บลิงก์เอกสารจากเดือน")
        run_collect_month_urls(page)


@task
def run_read_document_content_task():
    with browser() as b:
        page = b.new_page()
        print("📌 Stage 4: อ่านเนื้อหาเอกสาร")
        run_read_document_content(page)


@task
def run_filter_documents_task():
    print("📌 Stage 5: กรองข้อมูลที่สมบูรณ์")
    run_filter_documents()

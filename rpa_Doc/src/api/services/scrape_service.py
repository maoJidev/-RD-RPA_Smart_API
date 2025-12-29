# src/api/services/scrape_service.py
import subprocess
import logging

logger = logging.getLogger(__name__)

class ScrapeService:
    def __init__(self):
        self.stages = {
            1: "run_year",
            2: "run_month",
            3: "run_collect_month_urls_task",
            4: "run_read_document_content_task",
            5: "run_filter_documents_task",
            6: "run_filter_documents_by_title_task",
            7: "run_summarize_filtered_documents_task",
            8: "run_cleanup"
        }

    def get_task_name(self, stage: int) -> str:
        return self.stages.get(stage)

    def run_task(self, task_name: str):
        logger.info(f"Starting task: {task_name}")

        try:
            result = subprocess.run(
                ["python", "-m", "robocorp.tasks", "run", "tasks.py", "-t", task_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=r"D:\InternShip\project\RPA\rpa_Doc"
            )

            if result.returncode == 0:
                logger.info(f"{task_name} completed successfully.")
                if result.stdout:
                    logger.info(result.stdout)
                if result.stderr:
                    # robocorp บางครั้งส่ง warning มาที่ stderr
                    logger.warning(result.stderr)
            else:
                logger.error(f"{task_name} failed (code={result.returncode})")
                if result.stdout:
                    logger.error("----- STDOUT -----\n" + result.stdout)
                if result.stderr:
                    logger.error("----- STDERR -----\n" + result.stderr)

        except Exception:
            logger.exception("Subprocess execution failed")

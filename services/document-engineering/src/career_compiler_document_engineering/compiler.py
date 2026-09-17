import logging
import uuid
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class HtmlToPdfCompiler:
    """
    Compiles HTML into PDFs using Playwright via a Docker container.
    This avoids local macOS installation issues with greenlet/playwright on Python 3.14.
    """
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
    def compile(self, html_content: str) -> dict:
        """
        Compiles HTML string and returns a dict with paths to the resulting pdf.
        """
        job_id = str(uuid.uuid4())
        workdir = self.upload_dir / job_id
        workdir.mkdir(parents=True, exist_ok=True)
        
        html_path = workdir / "resume.html"
        pdf_path = workdir / "resume.pdf"
        
        try:
            # Write the HTML content to a file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            logger.info(f"Starting Playwright Docker compilation for {job_id}")
            
            # Use docker run to compile the HTML to PDF
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{workdir.absolute()}:/workdir",
                "mcr.microsoft.com/playwright:v1.40.0-jammy",
                "npx", "-y", "playwright@1.40.0", "pdf", "/workdir/resume.html", "/workdir/resume.pdf"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, timeout=600)
            
            if pdf_path.exists():
                return {
                    "status": "success",
                    "pdf_path": str(pdf_path.absolute()),
                    "log_path": None,
                }
            else:
                return {
                    "status": "failed",
                    "error": "PDF not generated",
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "Compilation timed out (perhaps docker pull took too long)"}
        except subprocess.CalledProcessError as e:
            logger.error(f"Compilation failed for {job_id}: {e.stderr.decode()}")
            return {"status": "failed", "error": e.stderr.decode()}
        except Exception as e:
            logger.error(f"Compilation failed for {job_id}: {e}")
            return {"status": "failed", "error": str(e)}

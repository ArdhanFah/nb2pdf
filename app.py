import importlib
import json
import os
import sys
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import nbformat

import nb2pdf.converter as converter
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = converter.TEMPLATES_DIR
BASE_DIR = Path(__file__).parent.resolve()
WEB_DIR = BASE_DIR / "web"
SAMPLE_NOTEBOOK_PATH = BASE_DIR / "tests" / "sample.ipynb"


class NeobrutalismRequestHandler(BaseHTTPRequestHandler):

    def _send_response(self, content, content_type="text/html", code=200):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            index_file = WEB_DIR / "index.html"
            with open(index_file, "r", encoding="utf-8") as f:
                self._send_response(f.read(), "text/html")
        elif self.path == "/style.css":
            css_file = WEB_DIR / "style.css"
            with open(css_file, "r", encoding="utf-8") as f:
                self._send_response(f.read(), "text/css")
        elif self.path == "/app.js":
            js_file = WEB_DIR / "app.js"
            with open(js_file, "r", encoding="utf-8") as f:
                self._send_response(f.read(), "application/javascript")
        elif self.path == "/api/demo":
            if SAMPLE_NOTEBOOK_PATH.exists():
                with open(SAMPLE_NOTEBOOK_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._send_response(json.dumps(data), "application/json")
            else:
                self._send_response(json.dumps({"error": "Demo notebook not found"}), "application/json", 404)
        else:
            self._send_response("404 Not Found", "text/plain", 404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            payload = json.loads(body)
        except Exception:
            self._send_response(json.dumps({"error": "Invalid JSON payload"}), "application/json", 400)
            return

        if self.path == "/api/preview":
            self.handle_preview(payload)
        elif self.path == "/api/convert":
            self.handle_convert(payload)
        else:
            self._send_response("404 Not Found", "text/plain", 404)

    def handle_preview(self, payload):
        importlib.reload(converter)
        ipynb_str = payload.get("ipynb", "")
        title = payload.get("title", "Jupyter Notebook")
        footer_text = payload.get("footer_text", "ArdhanFah")
        footer_url = payload.get("footer_url", "https://github.com/ArdhanFah")
        student_name = payload.get("student_name", "").strip()
        student_nim = payload.get("student_nim", "").strip()
        student_class = payload.get("student_class", "").strip()

        try:
            nb = nbformat.reads(ipynb_str, as_version=4)
        except Exception as e:
            self._send_response(f"Error parsing notebook: {str(e)}", "text/plain", 400)
            return

        processed_cells = []
        for cell in nb.cells:
            cell_dict = {
                "cell_type": cell.cell_type,
                "source": cell.source,
            }
            if cell.cell_type == "markdown":
                cell_dict["rendered_html"] = converter.render_md(
                    cell.source,
                    student_name=student_name,
                    student_nim=student_nim,
                    student_class=student_class
                )
            elif cell.cell_type == "code":
                cell_dict["outputs"] = cell.get("outputs", [])
            processed_cells.append(cell_dict)

        css_file = converter.TEMPLATES_DIR / "neobrutalism.css"
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()

        env = Environment(loader=FileSystemLoader(str(converter.TEMPLATES_DIR)))
        template = env.get_template("neobrutalism.html.j2")
        rendered_html = template.render(
            notebook_title=title,
            cells=processed_cells,
            css_content=css_content,
            footer_text=footer_text,
            footer_url=footer_url,
            student_name=student_name,
            student_nim=student_nim,
            student_class=student_class
        )

        self._send_response(rendered_html, "text/html")

    def handle_convert(self, payload):
        importlib.reload(converter)
        ipynb_str = payload.get("ipynb", "")
        title = payload.get("title", "").strip()
        filename = payload.get("filename", "notebook.ipynb").strip()
        footer_text = payload.get("footer_text", "ArdhanFah")
        footer_url = payload.get("footer_url", "https://github.com/ArdhanFah")
        student_name = payload.get("student_name", "").strip()
        student_nim = payload.get("student_nim", "").strip()
        student_class = payload.get("student_class", "").strip()

        if not title or title.lower().startswith("tmp"):
            if filename and not filename.lower().startswith("tmp"):
                title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
            else:
                title = "Jupyter Notebook"

        tmp_in_fd, tmp_in_path = tempfile.mkstemp(suffix=".ipynb")
        with open(tmp_in_fd, "w", encoding="utf-8") as f:
            f.write(ipynb_str)

        tmp_out_fd, tmp_out_path = tempfile.mkstemp(suffix=".pdf")
        os.close(tmp_out_fd)

        try:
            converter.convert(
                ipynb_path=tmp_in_path,
                output_path=tmp_out_path,
                notebook_title=title,
                footer_text=footer_text,
                footer_url=footer_url,
                student_name=student_name,
                student_nim=student_nim,
                student_class=student_class
            )

            with open(tmp_out_path, "rb") as f:
                pdf_bytes = f.read()

            download_filename = title.replace(" ", "_") + "_report.pdf"

            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Disposition", f'attachment; filename="{download_filename}"')
            self.send_header("Content-Length", str(len(pdf_bytes)))
            self.end_headers()
            self.wfile.write(pdf_bytes)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_response(json.dumps({"error": f"{str(e)}"}), "application/json", 500)
        finally:
            if os.path.exists(tmp_in_path):
                try:
                    os.remove(tmp_in_path)
                except Exception:
                    pass
            if os.path.exists(tmp_out_path):
                try:
                    os.remove(tmp_out_path)
                except Exception:
                    pass


def run_server(port=5000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, NeobrutalismRequestHandler)
    print(f"⚡ nb2pdf Web Application running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server(port)

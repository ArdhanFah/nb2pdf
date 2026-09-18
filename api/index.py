import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys
import os

# Add root project path so nb2pdf can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import nbformat
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import nb2pdf.converter as converter

class handler(BaseHTTPRequestHandler):

    def _send(self, content, content_type="text/html", code=200):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self._send("", "text/plain", 200)

    def do_GET(self):
        if self.path.endswith("/api/demo"):
            demo_path = Path(__file__).parent.parent / "tests" / "sample.ipynb"
            if demo_path.exists():
                with open(demo_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._send(json.dumps(data), "application/json")
            else:
                self._send(json.dumps({"error": "Demo not found"}), "application/json", 404)
        else:
            self._send("nb2pdf API", "text/plain", 200)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(body)
        except Exception:
            self._send(json.dumps({"error": "Invalid JSON"}), "application/json", 400)
            return

        ipynb_str = payload.get("ipynb", "")
        title = payload.get("title", "Jupyter Notebook")
        student_name = payload.get("student_name", "").strip()
        student_nim = payload.get("student_nim", "").strip()
        student_class = payload.get("student_class", "").strip()
        show_cover = payload.get("show_cover", True)

        try:
            nb = nbformat.reads(ipynb_str, as_version=4)
        except Exception as e:
            self._send(f"Error parsing notebook: {str(e)}", "text/plain", 400)
            return

        if self.path.endswith("/api/preview") or self.path.endswith("/api/convert"):
            processed_cells = converter.process_notebook_cells(
                nb.cells,
                student_name=student_name,
                student_nim=student_nim,
                student_class=student_class
            )

            css_file = converter.TEMPLATES_DIR / "neobrutalism.css"
            with open(css_file, "r", encoding="utf-8") as f:
                css_content = f.read()

            env = Environment(loader=FileSystemLoader(str(converter.TEMPLATES_DIR)))
            template = env.get_template("neobrutalism.html.j2")
            rendered_html = template.render(
                notebook_title=title,
                cells=processed_cells,
                css_content=css_content,
                footer_text="ArdhanFah",
                footer_url="https://github.com/ArdhanFah",
                student_name=student_name,
                student_nim=student_nim,
                student_class=student_class,
                show_cover=show_cover
            )

            if self.path.endswith("/api/preview"):
                self._send(rendered_html, "text/html")
            else:
                pdf_bytes = HTML(string=rendered_html, base_url=str(converter.TEMPLATES_DIR)).write_pdf()
                self._send(pdf_bytes, "application/pdf")
        else:
            self._send("Not Found", "text/plain", 404)

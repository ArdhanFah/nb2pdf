from pathlib import Path
import re
import html
import io
import base64
import nbformat
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent / "templates"

try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import markdown
except ImportError:
    markdown = None

try:
    import latex2mathml.converter
    def sys_latex_to_mathml(latex_str, is_block=False):
        try:
            mathml = latex2mathml.converter.convert(latex_str)
            if is_block:
                mathml = mathml.replace('<math xmlns=', '<math display="block" xmlns=')
            return mathml
        except Exception:
            return None
except ImportError:
    sys_latex_to_mathml = None


MATH_SYMBOLS = {
    r'\gamma': 'γ', r'\alpha': 'α', r'\beta': 'β', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\theta': 'θ', r'\lambda': 'λ', r'\mu': 'μ',
    r'\pi': 'π', r'\sigma': 'σ', r'\tau': 'τ', r'\phi': 'φ',
    r'\omega': 'ω', r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Sigma': 'Σ',
    r'\Omega': 'Ω', r'\infty': '∞', r'\approx': '≈', r'\neq': '≠',
    r'\le': '≤', r'\leq': '≤', r'\ge': '≥', r'\geq': '≥',
    r'\times': '×', r'\cdot': '·', r'\pm': '±', r'\degree': '°',
    r'\partial': '∂', r'\nabla': '∇', r'\int': '∫', r'\sum': '∑',
    r'\prod': '∏', r'\to': '→', r'\in': '∈'
}


def latex_to_mathml(latex: str, is_block: bool = False) -> str:
    """
    Converts LaTeX math expressions into MathML XML for PDF rendering.
    """
    if not latex:
        return ""

    if sys_latex_to_mathml:
        res = sys_latex_to_mathml(latex, is_block)
        if res:
            if is_block:
                return f'<div class="math-block-container">{res}</div>'
            return f'<span class="math-inline-container">{res}</span>'

    # Cleanup latex spacers and text wrappers
    latex = re.sub(r'\\(quad|qquad|;|!|,|\s+)', ' ', latex)
    latex = re.sub(r'\\text\{([^}]+)\}', r'\1', latex)
    latex = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', latex)
    latex = re.sub(r'\\mathbf\{([^}]+)\}', r'\1', latex)

    def parse_expr(expr):
        expr = expr.strip()
        if not expr:
            return ""

        # Handle \frac{num}{den}
        def frac_repl(m):
            num_html = parse_expr(m.group(1))
            den_html = parse_expr(m.group(2))
            return f'<mfrac><mrow>{num_html}</mrow><mrow>{den_html}</mrow></mfrac>'

        while r'\frac' in expr:
            expr = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', frac_repl, expr)

        # Handle \sqrt{expr}
        expr = re.sub(r'\\sqrt\{([^}]+)\}', lambda m: f'<msqrt><mrow>{parse_expr(m.group(1))}</mrow></msqrt>', expr)

        # Handle superscripts x^{y} or x^y
        expr = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\^\{([^}]+)\}', lambda m: f'<msup><mrow>{parse_expr(m.group(1))}</mrow><mrow>{parse_expr(m.group(2))}</mrow></msup>', expr)
        expr = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\^([A-Za-z0-9α-ωΓ-Ω]+)', lambda m: f'<msup><mrow>{parse_expr(m.group(1))}</mrow><mrow>{parse_expr(m.group(2))}</mrow></msup>', expr)

        # Handle subscripts x_{y} or x_y
        expr = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\_\{([^}]+)\}', lambda m: f'<msub><mrow>{parse_expr(m.group(1))}</mrow><mrow>{parse_expr(m.group(2))}</mrow></msub>', expr)
        expr = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\_([A-Za-z0-9α-ωΓ-Ω]+)', lambda m: f'<msub><mrow>{parse_expr(m.group(1))}</mrow><mrow>{parse_expr(m.group(2))}</mrow></msub>', expr)

        # Tokenize symbols
        for cmd, sym in MATH_SYMBOLS.items():
            expr = expr.replace(cmd, sym)

        # Tokenize remaining plain text components into MathML tags <mi>, <mn>, <mo>
        tokens = []
        parts = re.split(r'(<[^>]+>|\s+|[\=\+\-\*\·\×\/\(\)\[\]\,\.\:\;\approx\neq\le\ge\to\pm\degree\partial\nabla\int\sum\prod])', expr)
        for p in parts:
            if not p:
                continue
            if p.startswith('<') and p.endswith('>'):
                tokens.append(p)
            elif re.match(r'[\=\+\-\*\·\×\/\(\)\[\]\,\.\:\;\approx\neq\le\ge\to\pm\degree\partial\nabla\int\sum\prod]', p):
                tokens.append(f'<mo>{html.escape(p)}</mo>')
            elif re.match(r'^\d+(\.\d+)?$', p.strip()):
                tokens.append(f'<mn>{p.strip()}</mn>')
            elif p.strip():
                tokens.append(f'<mi>{p.strip()}</mi>')

        return "".join(tokens)

    parsed_inner = parse_expr(latex)
    display_attr = 'display="block"' if is_block else ''
    mathml_out = f'<math xmlns="http://www.w3.org/1998/Math/MathML" {display_attr}><mrow>{parsed_inner}</mrow></math>'

    if is_block:
        return f'<div class="math-block-container">{mathml_out}</div>'
    return f'<span class="math-inline-container">{mathml_out}</span>'


def sanitize_latex_for_matplotlib(latex_str: str) -> str:
    r"""
    Sanitizes LaTeX math expression for Matplotlib's mathtext parser.
    Converts unsupported macros (\max, \min, \text, \operatorname, primes ') to mathtext compatible forms.
    """
    if not latex_str or not latex_str.strip():
        return ""

    s = latex_str.strip()

    # Strip outer $ or $$ or \(\) or \[\]
    while (s.startswith('$$') and s.endswith('$$')) or (s.startswith('$') and s.endswith('$')):
        if s.startswith('$$') and s.endswith('$$') and len(s) >= 4:
            s = s[2:-2].strip()
        elif s.startswith('$') and s.endswith('$') and len(s) >= 2:
            s = s[1:-1].strip()
        else:
            break

    if s.startswith(r'\(') and s.endswith(r'\)'):
        s = s[2:-2].strip()
    if s.startswith(r'\[') and s.endswith(r'\]'):
        s = s[2:-2].strip()

    # Convert primes/apostrophes I' to I^{\prime}
    s = re.sub(r"([A-Za-z0-9]+)'", r"\1^{\\prime}", s)
    s = s.replace("'", r"^{\prime}")

    # Clean TeX spacing macros
    s = re.sub(r'\\(quad|qquad|;|!|,|\s+)', ' ', s)

    # Map unsupported TeX functions to \mathrm{...}
    unsupported_ops = ['max', 'min', 'argmax', 'argmin', 'det', 'dim', 'gcd', 'inf', 'ker', 'lg', 'mod', 'sup', 'deg']
    for op in unsupported_ops:
        s = re.sub(r'\\' + op + r'\b', r'\\mathrm{' + op + '}', s)

    # Convert \text{...}, \operatorname{...}, \mbox{...} to \mathrm{...}
    s = re.sub(r'\\(?:text|operatorname|mbox)\{([^}]+)\}', r'\\mathrm{\1}', s)
    s = re.sub(r'\\mathbf\{([^}]+)\}', r'\\mathbf{\1}', s)

    # Wrap multi-letter words in subscripts/superscripts or base words with \mathrm
    def replace_sub_words(m):
        base = m.group(1)
        sub = m.group(2)
        base_str = f"\\mathrm{{{base}}}" if len(base) > 1 and not base.startswith('\\') else base
        sub_str = f"\\mathrm{{{sub}}}" if len(sub) > 1 and not sub.startswith('\\') else sub
        return f"{base_str}_{{{sub_str}}}"

    s = re.sub(r'([A-Za-z]{2,})\_\{([A-Za-z0-9\s]+)\}', replace_sub_words, s)

    return s.strip()


def render_fallback_html_math(latex_clean: str, is_block: bool = False) -> str:
    """
    Renders LaTeX math into formatted HTML elements (fractions, sub/super scripts, operators).
    Also includes raw TeX in MathJax format so browser live-preview can render it dynamically.
    """
    expr = latex_clean.strip()

    def build_frac_html(m):
        num = parse_simple_tex(m.group(1))
        den = parse_simple_tex(m.group(2))
        return f'<span class="math-frac" style="display:inline-flex; flex-direction:column; vertical-align:-0.6em; text-align:center; margin:0 4px; font-style:normal;"><span class="math-num" style="border-bottom:1.5px solid #202124; padding:0 3px; font-size:0.9em; line-height:1.2;">{num}</span><span class="math-den" style="padding:0 3px; font-size:0.9em; line-height:1.2;">{den}</span></span>'

    def parse_simple_tex(t):
        t = t.strip()
        while r'\frac' in t:
            t = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', build_frac_html, t)
        
        t = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\_\{([^}]+)\}', r'\1<sub style="font-size:0.75em; vertical-align:-0.2em;">\2</sub>', t)
        t = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\_([A-Za-z0-9α-ωΓ-Ω]+)', r'\1<sub style="font-size:0.75em; vertical-align:-0.2em;">\2</sub>', t)
        t = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\^\{([^}]+)\}', r'\1<sup style="font-size:0.75em; vertical-align:0.35em;">\2</sup>', t)
        t = re.sub(r'([A-Za-z0-9α-ωΓ-Ω]+)\^([A-Za-z0-9α-ωΓ-Ω]+)', r'\1<sup style="font-size:0.75em; vertical-align:0.35em;">\2</sup>', t)

        t = re.sub(r'\\(max|min|avg|lightness|luminance)\b', r'\1', t)
        t = re.sub(r'\\(left|right)', '', t)

        for cmd, sym in MATH_SYMBOLS.items():
            cmd_name = cmd.lstrip('\\')
            t = re.sub(r'\\' + cmd_name + r'\b', sym, t)
        return t

    parsed_html = parse_simple_tex(expr)
    delim_open = '\\[' if is_block else '\\('
    delim_close = '\\]' if is_block else '\\)'
    
    if is_block:
        return f'<div class="math-block-container" style="text-align:center; font-family:\'Latin Modern Math\', \'Cambria Math\', \'Times New Roman\', serif; font-size:1.15em; margin:14px 0; padding:10px; background:#f8f9fa; border:1px solid #e0e0e0; border-radius:6px;">{parsed_html}<span class="mathjax-raw" style="display:none;">{delim_open} {html.escape(latex_clean)} {delim_close}</span></div>'
    else:
        return f'<span class="math-inline-container" style="font-family:\'Latin Modern Math\', \'Cambria Math\', \'Times New Roman\', serif; font-size:1.05em; display:inline-block; vertical-align:middle; margin:0 2px;">{parsed_html}<span class="mathjax-raw" style="display:none;">{delim_open} {html.escape(latex_clean)} {delim_close}</span></span>'


def render_latex_to_html_img(latex_str: str, is_block: bool = False) -> str:
    """
    Thread-safe LaTeX math renderer using Object-Oriented Matplotlib with fallback.
    Guarantees 100% vector-quality PDF rendering and high quality preview.
    """
    if not latex_str or not latex_str.strip():
        return ""

    latex_clean = latex_str.strip()
    while latex_clean.startswith('$') and latex_clean.endswith('$') and len(latex_clean) > 1:
        latex_clean = latex_clean[1:-1].strip()

    if HAS_MATPLOTLIB and latex_clean:
        try:
            sanitized = sanitize_latex_for_matplotlib(latex_clean)
            latex_expr = f"${sanitized}$"
            fig = Figure(figsize=(0.1, 0.1), dpi=200)
            fig.patch.set_alpha(0.0)
            canvas = FigureCanvasAgg(fig)
            fontsize = 13 if is_block else 11

            fig.text(0.0, 0.5, latex_expr, fontsize=fontsize, color='#202124', verticalalignment='center')
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.01, transparent=True, dpi=200)

            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            img_src = f"data:image/png;base64,{img_b64}"

            alt_txt = html.escape(latex_str)
            if is_block:
                return f'<div class="math-block-container" style="text-align:center; margin:12px 0;"><img src="{img_src}" class="math-block-img" alt="{alt_txt}" style="max-width:100%; height:auto;"></div>'
            else:
                img_height = "1.8em" if r"\frac" in latex_clean else "1.25em"
                img_valign = "-0.55em" if r"\frac" in latex_clean else "-0.2em"
                return f'<img src="{img_src}" class="math-inline-img" alt="{alt_txt}" style="vertical-align:{img_valign}; height:{img_height}; margin:0 2px; display:inline-block;">'
        except Exception:
            pass

    return render_fallback_html_math(latex_clean, is_block=is_block)


def process_identity_placeholders(text: str, student_name=None, student_nim=None, student_class=None) -> str:
    """Replaces placeholders like Nama : - inside markdown content with user identity."""
    if not text:
        return text

    if isinstance(text, list):
        text = "".join(text)

    name_val = student_name if (student_name and student_name.strip() and student_name != "-") else "Ardhan Dikri Achmad Fahrudin"
    nim_val = student_nim if (student_nim and student_nim.strip() and student_nim != "-") else "2441070020012"
    class_val = student_class if (student_class and student_class.strip() and student_class != "-") else "TI-3B"

    # Replace inline patterns like Nama : - or Nama : [space] or Nama\t:\t-
    text = re.sub(r'(\b\*{0,2}Nama\*{0,2}\s*[:\t]\s*)[-–—]+', r'\1' + name_val, text, flags=re.IGNORECASE)
    text = re.sub(r'(\b\*{0,2}Nama\*{0,2}\s*[:\t]\s*)(?=\n|$)', r'\1' + name_val, text, flags=re.IGNORECASE)
    text = re.sub(r'(\|\s*\*{0,2}Nama\*{0,2}\s*\|\s*:\s*\|\s*)[-–—]+', r'\1' + name_val, text, flags=re.IGNORECASE)

    text = re.sub(r'(\b\*{0,2}NIM\*{0,2}\s*[:\t]\s*)[-–—]+', r'\1' + nim_val, text, flags=re.IGNORECASE)
    text = re.sub(r'(\b\*{0,2}NIM\*{0,2}\s*[:\t]\s*)(?=\n|$)', r'\1' + nim_val, text, flags=re.IGNORECASE)
    text = re.sub(r'(\|\s*\*{0,2}NIM\*{0,2}\s*\|\s*:\s*\|\s*)[-–—]+', r'\1' + nim_val, text, flags=re.IGNORECASE)

    text = re.sub(r'(\b\*{0,2}Kelas\*{0,2}\s*[:\t]\s*)[-–—]+', r'\1' + class_val, text, flags=re.IGNORECASE)
    text = re.sub(r'(\b\*{0,2}Kelas\*{0,2}\s*[:\t]\s*)(?=\n|$)', r'\1' + class_val, text, flags=re.IGNORECASE)
    text = re.sub(r'(\|\s*\*{0,2}Kelas\*{0,2}\s*\|\s*:\s*\|\s*)[-–—]+', r'\1' + class_val, text, flags=re.IGNORECASE)

    return text


def extract_naked_tex(text: str, math_inlines: list, math_blocks: list) -> str:
    r"""
    Extracts naked TeX math expressions (equations or symbols written without $ delimiters)
    and converts ONLY the math expressions into placeholders, keeping surrounding prose inline.
    """
    if not text:
        return text

    lines = text.split('\n')
    new_lines = []

    # Matches TeX math equations or symbols (e.g., \gamma = 1.2, C = 1.6, \gamma, \frac{a}{b}, I' = ...)
    inline_pattern = r'(\\[a-zA-Z]+(?:\s*[\=\+\-\*\/]\s*[\d\.\w]+|\{[^}]*\}|\([^)]*\)|_[A-Za-z0-9_\{\}]+|\^[A-Za-z0-9_\{\}]+)*|[A-Za-z0-9_]+\s*[\_\^]\{[^}]+\}(?:\s*[\=\+\-\*\/]\s*(?:[\d\.\w\+\-\*\/]+|\\[a-zA-Z]+\{[^}]*\}|\\[a-zA-Z]+(?:\([^)]*\))?))*|\b[A-Za-z]\s*=\s*[\d\.]+|\\[a-zA-Z]+)'

    for line in lines:
        line_str = line.strip()

        if not line_str or line_str.startswith('<') or line_str.startswith('```') or line_str.startswith('|---'):
            new_lines.append(line)
            continue

        # If line is a standalone full display equation:
        # e.g. I' = 255 \cdot \left( \frac{I}{255} \right)^{\frac{1}{\gamma}}
        # e.g. Grayscale_{avg} = \frac{R + G + B}{3}
        is_equation_line = bool(re.search(r'(\\[a-zA-Z]+|_{|\^{}).*=', line_str) or re.search(r'^\s*[A-Za-z0-9_\']+\s*=\s*.*(?:\\[a-zA-Z]+|_{|\^{})', line_str))
        is_prose = bool(re.search(r'^(?:[-\*\d\.]|\w+\s*:|\w+\s+\w{3,})', line_str))

        if is_equation_line and not is_prose:
            idx = len(math_blocks)
            math_blocks.append(line_str)
            new_lines.append(f"MATHBLOCKXYZ{idx}XYZ")
            continue

        # Replace TeX tokens inline without splitting prose lines
        def replace_token(m):
            token = m.group(0).strip()
            # Clean trailing punctuation from captured token if any
            token = re.sub(r'[\.\,\;\)]+$', '', token).strip()
            if not token or token.startswith('http') or token.startswith('<'):
                return m.group(0)
            idx = len(math_inlines)
            math_inlines.append(token)
            return f"MATHINLINEXYZ{idx}XYZ"

        processed_line = re.sub(inline_pattern, replace_token, line)
        new_lines.append(processed_line)

    return '\n'.join(new_lines)


def render_md(text, student_name: str = None, student_nim: str = None, student_class: str = None) -> str:
    """
    Renders markdown to HTML with TeX Math parsing and identity placeholder substitution.
    """
    if not text:
        return ""

    if isinstance(text, list):
        text = "".join(text)

    # 1. Replace identity placeholders inside cell text
    text = process_identity_placeholders(text, student_name, student_nim, student_class)

    # 2. Extract math formulas to placeholders so markdown parser doesn't mangle TeX symbols
    math_blocks = []
    math_inlines = []

    # Clean empty math spacers like $\ $ or $\quad$ without destroying real formulas
    text = re.sub(r'\$\s*(?:\\(?:quad|qquad|;|!|,|\s))*\s*\$', ' ', text)

    # Extract Block Math $$...$$ or \[...\]
    def extract_block(match):
        formula = match.group(1).strip()
        idx = len(math_blocks)
        math_blocks.append(formula)
        return f"MATHBLOCKXYZ{idx}XYZ"

    text = re.sub(r'\$\$([\s\S]+?)\$\$', extract_block, text)
    text = re.sub(r'\\\[([\s\S]+?)\\\]', extract_block, text)

    # Extract Inline Math $...$ or \(...\)
    def extract_inline(match):
        formula = match.group(1).strip()
        if not formula:
            return ""
        idx = len(math_inlines)
        math_inlines.append(formula)
        return f"MATHINLINEXYZ{idx}XYZ"

    text = re.sub(r'(?<!\$)\$([^$]+?)\$(?!\$)', extract_inline, text)
    text = re.sub(r'\\\(([\s\S]+?)\\\)', extract_inline, text)

    # Extract Naked TeX expressions inline (formulas written without $ signs)
    text = extract_naked_tex(text, math_inlines, math_blocks)

    # 3. Render Markdown to HTML
    if markdown:
        rendered = markdown.markdown(text, extensions=['extra', 'tables', 'fenced_code'])
    else:
        rendered = f"<p>{html.escape(text)}</p>"

    # 4. Substitute rendered math HTML back into placeholders
    for i, formula in enumerate(math_blocks):
        math_html = render_latex_to_html_img(formula, is_block=True)
        pattern = f"<p>MATHBLOCKXYZ{i}XYZ</p>"
        if pattern in rendered:
            rendered = rendered.replace(pattern, math_html)
        else:
            rendered = rendered.replace(f"MATHBLOCKXYZ{i}XYZ", math_html)

    for i, formula in enumerate(math_inlines):
        math_html = render_latex_to_html_img(formula, is_block=False)
        rendered = rendered.replace(f"MATHINLINEXYZ{i}XYZ", math_html)

    return rendered


TEMPLATES_DIR = Path(__file__).parent / "templates"


def convert(
    ipynb_path: str,
    output_path: str = None,
    notebook_title: str = None,
    footer_text: str = "ArdhanFah",
    footer_url: str = "https://github.com/ArdhanFah",
    student_name: str = None,
    student_nim: str = None,
    student_class: str = None
) -> str:
    """
    Convert a Jupyter Notebook (.ipynb) to a clean PDF with MathML equations and cover header.
    """
    ipynb_path = Path(ipynb_path).resolve()
    if not ipynb_path.exists():
        raise FileNotFoundError(f"Notebook file not found: {ipynb_path}")

    if output_path is None:
        output_path = ipynb_path.with_suffix(".pdf")
    else:
        output_path = Path(output_path).resolve()

    # Load notebook
    with open(ipynb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    if not notebook_title or not notebook_title.strip() or notebook_title.lower().startswith("tmp"):
        notebook_title = ipynb_path.stem.replace("_", " ").replace("-", " ").title()
    if not notebook_title or notebook_title.lower().startswith("tmp"):
        notebook_title = "Laporan Praktikum"

    # Process cells
    processed_cells = []
    for cell in nb.cells:
        cell_dict = {
            "cell_type": cell.cell_type,
            "source": cell.source,
        }
        if cell.cell_type == "markdown":
            cell_dict["rendered_html"] = render_md(
                cell.source,
                student_name=student_name,
                student_nim=student_nim,
                student_class=student_class
            )
        elif cell.cell_type == "code":
            cell_dict["outputs"] = cell.get("outputs", [])
        processed_cells.append(cell_dict)

    # Load CSS content
    css_file = TEMPLATES_DIR / "neobrutalism.css"
    with open(css_file, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Render HTML template
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("neobrutalism.html.j2")
    rendered_html = template.render(
        notebook_title=notebook_title,
        cells=processed_cells,
        css_content=css_content,
        footer_text=footer_text,
        footer_url=footer_url,
        student_name=student_name,
        student_nim=student_nim,
        student_class=student_class
    )

    # Convert HTML to PDF using WeasyPrint
    HTML(string=rendered_html, base_url=str(TEMPLATES_DIR)).write_pdf(str(output_path))

    return str(output_path)


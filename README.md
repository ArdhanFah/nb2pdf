# nb2pdf

Convert Jupyter Notebook (`.ipynb`) files to stunning PDFs styled with a **Neobrutalism** theme, complete with a custom clickable footer linking to [github.com/ArdhanFah](https://github.com/ArdhanFah).

## Features
- 🎨 **Neobrutalism Aesthetic**: Bold high-contrast borders, raw vivid colors, thick drop shadows, and clean retro typography.
- 🔗 **Clickable Footer**: Every page includes a footer linking directly to `https://github.com/ArdhanFah`.
- ⚡ **High Quality PDF Output**: Built using WeasyPrint for pixel-perfect PDF rendering with full CSS `@page` support.

## Installation

```bash
pip install -e .
```

## Usage

```bash
nb2pdf notebook.ipynb -o output.pdf
```

Or run via python module:

```bash
python -m nb2pdf notebook.ipynb -o output.pdf
```

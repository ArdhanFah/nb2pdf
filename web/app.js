document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const loadDemoBtn = document.getElementById('loadDemoBtn');
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    const statusMsg = document.getElementById('statusMsg');
    const previewCanvas = document.getElementById('previewCanvas');
    const emptyState = document.getElementById('emptyState');
    const previewIframe = document.getElementById('previewIframe');
    
    // Identity & Title inputs
    const showCoverHeader = document.getElementById('showCoverHeader');
    const docTitle = document.getElementById('docTitle');
    const studentName = document.getElementById('studentName');
    const studentNim = document.getElementById('studentNim');
    const studentClass = document.getElementById('studentClass');
    const saveIdentityBtn = document.getElementById('saveIdentityBtn');
    const saveStatus = document.getElementById('saveStatus');
    const footerLinkBadge = document.getElementById('footerLinkBadge');

    let currentFileContent = null;
    let currentFileName = null;

    // 1. Restore saved values from localStorage or default values
    const savedShowCover = localStorage.getItem('nb2pdf_show_cover');
    const savedTitle = localStorage.getItem('nb2pdf_doc_title');
    const savedName = localStorage.getItem('nb2pdf_student_name');
    const savedNim = localStorage.getItem('nb2pdf_student_nim');
    const savedClass = localStorage.getItem('nb2pdf_student_class');

    if (showCoverHeader && savedShowCover !== null) showCoverHeader.checked = (savedShowCover === 'true');
    if (docTitle && savedTitle) docTitle.value = savedTitle;
    if (studentName) studentName.value = savedName || "Ardhan Dikri Achmad Fahrudin";
    if (studentNim) studentNim.value = savedNim || "2441070020012";
    if (studentClass) studentClass.value = savedClass || "TI-3B";

    function formatTitleFromFilename(name) {
        if (!name) return "";
        return name
            .replace(/\.ipynb$/i, '')
            .replace(/[_-]/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    }

    // Helper to save all inputs to localStorage
    function saveIdentityToStorage() {
        if (showCoverHeader) localStorage.setItem('nb2pdf_show_cover', showCoverHeader.checked);
        if (docTitle) localStorage.setItem('nb2pdf_doc_title', docTitle.value);
        if (studentName) localStorage.setItem('nb2pdf_student_name', studentName.value);
        if (studentNim) localStorage.setItem('nb2pdf_student_nim', studentNim.value);
        if (studentClass) localStorage.setItem('nb2pdf_student_class', studentClass.value);
    }

    function showStatus(msg, type = 'info') {
        if (!statusMsg) return;
        statusMsg.textContent = msg;
        if (type === 'red') {
            statusMsg.style.color = '#d93025';
        } else if (type === 'green') {
            statusMsg.style.color = '#188038';
        } else {
            statusMsg.style.color = '#202124';
        }
    }

    // Save Identity Button Click Handler
    if (saveIdentityBtn) {
        saveIdentityBtn.addEventListener('click', () => {
            saveIdentityToStorage();
            if (saveStatus) {
                saveStatus.textContent = '✅ Identitas Berhasil Disimpan!';
                setTimeout(() => { saveStatus.textContent = ''; }, 3000);
            }

            if (currentFileContent) {
                fetchPreview();
            }
        });
    }

    // Real-time preview & storage update when typing in fields or toggling checkbox
    [showCoverHeader, docTitle, studentName, studentNim, studentClass].forEach(input => {
        if (input) {
            const eventName = input.type === 'checkbox' ? 'change' : 'input';
            input.addEventListener(eventName, () => {
                saveIdentityToStorage();
                if (currentFileContent) {
                    fetchPreview();
                }
            });
        }
    });

    // File Drag & Drop
    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
    }

    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', resetFile);
    }

    function handleFile(file) {
        if (!file.name.endsWith('.ipynb')) {
            showStatus('⚠️ Please upload a valid .ipynb file!', 'red');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            currentFileContent = e.target.result;
            currentFileName = file.name;
            fileName.textContent = file.name;
            dropZone.style.display = 'none';
            fileInfo.style.display = 'flex';
            exportPdfBtn.disabled = false;

            // Automatically format title from uploaded filename!
            const autoTitle = formatTitleFromFilename(file.name);
            if (docTitle) {
                docTitle.value = autoTitle;
                localStorage.setItem('nb2pdf_doc_title', autoTitle);
            }

            fetchPreview();
        };
        reader.readAsText(file);
    }

    function resetFile() {
        currentFileContent = null;
        currentFileName = null;
        if (fileInput) fileInput.value = '';
        dropZone.style.display = 'block';
        fileInfo.style.display = 'none';
        exportPdfBtn.disabled = true;
        emptyState.style.display = 'flex';
        previewIframe.style.display = 'none';
        showStatus('');
    }

    // Default Fallback Demo Data
    const fallbackDemo = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": [
                    "# Analisis Pengolahan Citra Digital\n",
                    "Dokumen ini memuat analisis koreksi gamma pada citra.\n\n",
                    "## Resiko Metode\n",
                    "Jika nilai $\\gamma$ terlalu kecil, noise di area gelap akan ikut diperkuat sehingga citra tampak berbintik-bintik (grainy).\n\n",
                    "$$\\text{Output} = \\text{Input}^\\gamma$$"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "outputs": [
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": [
                            "Nilai gamma optimal: 0.4\n",
                            "Koreksi citra berhasil dilakukan.\n"
                        ]
                    }
                ],
                "source": [
                    "import numpy as np\n\n",
                    "def gamma_correction(image, gamma=1.0):\n",
                    "    invGamma = 1.0 / gamma\n",
                    "    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype(\"uint8\")\n",
                    "    return table\n\n",
                    "print(\"Nilai gamma optimal: 0.4\")\n",
                    "print(\"Koreksi citra berhasil dilakukan.\")"
                ]
            }
        ]
    };

    // Load Demo Notebook
    if (loadDemoBtn) {
        loadDemoBtn.addEventListener('click', async () => {
            showStatus('Loading demo notebook...');
            try {
                let data = null;
                try {
                    const res = await fetch('/api/demo');
                    if (res.ok) {
                        data = await res.json();
                    }
                } catch (_) {}

                if (!data) {
                    try {
                        const res = await fetch('./demo.json');
                        if (res.ok) {
                            data = await res.json();
                        }
                    } catch (_) {}
                }

                if (!data) {
                    data = fallbackDemo;
                }

                currentFileContent = JSON.stringify(data);
                currentFileName = 'sample_demo.ipynb';
                fileName.textContent = 'sample_demo.ipynb';
                dropZone.style.display = 'none';
                fileInfo.style.display = 'flex';
                exportPdfBtn.disabled = false;

                if (docTitle) {
                    docTitle.value = 'Demo Notebook Report';
                }

                fetchPreview();
            } catch (err) {
                showStatus('⚠️ Error loading demo: ' + err.message, 'red');
            }
        });
    }

    // Helper to gather payload data
    function getPayloadData() {
        saveIdentityToStorage();

        const sTitle = (docTitle && docTitle.value.trim()) ? docTitle.value.trim() : (currentFileName ? currentFileName.replace('.ipynb', '') : 'Jupyter Notebook');
        const sName = (studentName && studentName.value.trim()) ? studentName.value.trim() : (localStorage.getItem('nb2pdf_student_name') || 'Ardhan Dikri Achmad Fahrudin');
        const sNim = (studentNim && studentNim.value.trim()) ? studentNim.value.trim() : (localStorage.getItem('nb2pdf_student_nim') || '2441070020012');
        const sClass = (studentClass && studentClass.value.trim()) ? studentClass.value.trim() : (localStorage.getItem('nb2pdf_student_class') || 'TI-3B');

        return {
            ipynb: currentFileContent,
            title: sTitle,
            filename: currentFileName,
            footer_text: 'ArdhanFah',
            footer_url: 'https://github.com/ArdhanFah',
            student_name: sName,
            student_nim: sNim,
            student_class: sClass,
            show_cover: showCoverHeader ? showCoverHeader.checked : true
        };
    }

    // Simple Client-Side HTML Renderer for static GitHub Pages fallback
    function renderStaticPreviewHtml(payload) {
        let nb = {};
        try {
            nb = JSON.parse(payload.ipynb);
        } catch (e) {
            return `<html><body><h3>Error parsing notebook JSON</h3></body></html>`;
        }

        const title = payload.title || 'Jupyter Notebook';
        const name = payload.student_name || '';
        const nim = payload.student_nim || '';
        const sClass = payload.student_class || '';
        const showCover = (payload.show_cover !== false);

        let cellsHtml = '';
        (nb.cells || []).forEach((cell, idx) => {
            const srcArr = Array.isArray(cell.source) ? cell.source : [cell.source || ''];
            const srcText = srcArr.join('');

            if (cell.cell_type === 'markdown') {
                // Escape simple HTML
                let mdContent = srcText
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
                
                // Formats headers
                mdContent = mdContent.replace(/^### (.*$)/gim, '<h3>$1</h3>');
                mdContent = mdContent.replace(/^## (.*$)/gim, '<h2>$1</h2>');
                mdContent = mdContent.replace(/^# (.*$)/gim, '<h1>$1</h1>');
                mdContent = mdContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                mdContent = mdContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
                mdContent = mdContent.replace(/\n\n/g, '<br><br>');

                cellsHtml += `<div class="cell markdown-cell">${mdContent}</div>`;
            } else if (cell.cell_type === 'code') {
                const codeEscaped = srcText
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');

                let outputsHtml = '';
                (cell.outputs || []).forEach(out => {
                    if (out.output_type === 'stream' || out.text) {
                        const txt = Array.isArray(out.text) ? out.text.join('') : (out.text || '');
                        outputsHtml += `<pre class="stream-output">${txt.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`;
                    } else if (out.data && out.data['image/png']) {
                        outputsHtml += `<div class="image-output"><img src="data:image/png;base64,${out.data['image/png']}"></div>`;
                    }
                });

                cellsHtml += `
                    <div class="cell code-cell">
                        <div class="code-prompt">In [${cell.execution_count || ' '}]:</div>
                        <pre class="code-input"><code>${codeEscaped}</code></pre>
                        ${outputsHtml ? `<div class="code-outputs">${outputsHtml}</div>` : ''}
                    </div>
                `;
            }
        });

        const coverHtml = showCover ? `
    <div class="cover-container">
        <div class="cover-title">${title}</div>
        <div class="meta-table">
            <div class="meta-row"><span class="meta-label">NAMA</span><span class="meta-colon">:</span><span class="meta-value">${name}</span></div>
            <div class="meta-row"><span class="meta-label">NIM</span><span class="meta-colon">:</span><span class="meta-value">${nim}</span></div>
            <div class="meta-row"><span class="meta-label">KELAS</span><span class="meta-colon">:</span><span class="meta-value">${sClass}</span></div>
        </div>
    </div>` : '';

        const footerHtml = `
    <div style="margin-top: 36px; padding-top: 10px; border-top: 1.5px solid #BDC1C6; text-align: center; font-family: 'Google Sans', 'Roboto', sans-serif;">
        <div style="font-size: 9pt; color: #5F6368; margin-bottom: 3px;">
            © 2026 <strong style="color: #202124;">nb2pdf</strong> • Created by <strong style="color: #202124;">ArdhanFah</strong>
        </div>
        <a href="https://github.com/ArdhanFah" target="_blank" style="color: #1A73E8; font-weight: 700; text-decoration: none; font-size: 8.5pt;">🐙 github.com/ArdhanFah</a>
    </div>`;

        return `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>${title}</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { font-family: 'Google Sans', 'Roboto', sans-serif; background: #fff; color: #202124; padding: 24px; margin: 0; line-height: 1.6; }
        .cover-container { border: 1px solid #DADCE0; border-radius: 8px; background-color: #F8F9FA; padding: 18px 24px; margin-bottom: 24px; }
        .cover-title { font-size: 18pt; font-weight: 700; border-bottom: 2px solid #202124; padding-bottom: 6px; margin-bottom: 12px; text-transform: uppercase; }
        .meta-table { display: table; width: 100%; font-size: 10.5pt; }
        .meta-row { display: table-row; line-height: 1.8; }
        .meta-label { display: table-cell; font-weight: 700; color: #5F6368; width: 70px; text-transform: uppercase; }
        .meta-colon { display: table-cell; font-weight: 700; color: #5F6368; width: 15px; text-align: center; }
        .meta-value { display: table-cell; font-weight: 500; color: #202124; }
        .cell { margin-bottom: 18px; }
        .code-prompt { font-family: monospace; font-size: 9pt; color: #5F6368; font-weight: bold; margin-bottom: 4px; }
        pre.code-input { background: #F1F3F4; border: 1px solid #DADCE0; border-radius: 6px; padding: 12px; font-family: 'Fira Code', monospace; font-size: 9.5pt; overflow-x: auto; margin: 0 0 8px 0; }
        .stream-output { background: #FFFFFF; border-left: 3px solid #1A73E8; padding: 8px 12px; font-family: monospace; font-size: 9pt; margin: 4px 0; }
        .image-output img { max-width: 100%; border-radius: 4px; margin-top: 8px; }
    </style>
</head>
<body>
    ${coverHtml}
    <div class="notebook-container">
        ${cellsHtml}
    </div>
    ${footerHtml}
</body>
</html>`;
    }

    // Fetch Live Preview
    async function fetchPreview() {
        if (!currentFileContent) return;
        showStatus('Rendering live preview with cover...');

        const payload = getPayloadData();

        try {
            let htmlContent = null;

            try {
                const res = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    htmlContent = await res.text();
                }
            } catch (_) {}

            // Static Client-Side Fallback for GitHub Pages
            if (!htmlContent) {
                htmlContent = renderStaticPreviewHtml(payload);
            }

            // Reliable iframe DOM injection
            emptyState.style.display = 'none';
            previewIframe.style.display = 'block';

            const doc = previewIframe.contentDocument || previewIframe.contentWindow.document;
            doc.open();
            doc.write(htmlContent);
            doc.close();

            // Trigger MathJax typeset inside preview iframe if available
            setTimeout(() => {
                try {
                    const win = previewIframe.contentWindow;
                    if (win && win.MathJax && win.MathJax.typesetPromise) {
                        win.MathJax.typesetPromise();
                    }
                } catch (_) {}
            }, 200);

            showStatus('✨ Live Cover & Notebook Preview Ready!', 'green');
        } catch (err) {
            showStatus('❌ Preview error: ' + err.message, 'red');
        }
    }

    // Export PDF
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', async () => {
            if (!currentFileContent) return;

            exportPdfBtn.disabled = true;
            showStatus('⏳ Generating PDF...');

            const payload = getPayloadData();

            try {
                let pdfBlob = null;
                try {
                    const res = await fetch('/api/convert', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    if (res.ok) {
                        pdfBlob = await res.blob();
                    }
                } catch (_) {}

                if (pdfBlob) {
                    const url = window.URL.createObjectURL(pdfBlob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = (payload.title ? payload.title.replace(/[^a-z0-9]/gi, '_') : 'notebook') + '.pdf';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    showStatus('✅ PDF Downloaded Successfully!', 'green');
                } else {
                    // Fallback to browser print PDF on GitHub Pages static host
                    showStatus('ℹ️ Hosting statis: Membuka dialog Cetak PDF browser...', 'green');
                    const win = previewIframe.contentWindow;
                    if (win) {
                        win.focus();
                        win.print();
                    }
                }
            } catch (err) {
                showStatus('❌ Export PDF error: ' + err.message, 'red');
            } finally {
                exportPdfBtn.disabled = false;
            }
        });
    }
});

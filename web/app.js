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
    const savedTitle = localStorage.getItem('nb2pdf_doc_title');
    const savedName = localStorage.getItem('nb2pdf_student_name');
    const savedNim = localStorage.getItem('nb2pdf_student_nim');
    const savedClass = localStorage.getItem('nb2pdf_student_class');

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
        if (docTitle) localStorage.setItem('nb2pdf_doc_title', docTitle.value);
        if (studentName) localStorage.setItem('nb2pdf_student_name', studentName.value);
        if (studentNim) localStorage.setItem('nb2pdf_student_nim', studentNim.value);
        if (studentClass) localStorage.setItem('nb2pdf_student_class', studentClass.value);
    }

    // Save Identity Button Click Handler
    if (saveIdentityBtn) {
        saveIdentityBtn.addEventListener('click', () => {
            saveIdentityToStorage();
            saveStatus.textContent = '✅ Identitas Berhasil Disimpan!';
            setTimeout(() => { saveStatus.textContent = ''; }, 3000);

            if (currentFileContent) {
                fetchPreview();
            }
        });
    }

    // Real-time preview & storage update when typing in fields
    [docTitle, studentName, studentNim, studentClass].forEach(input => {
        if (input) {
            input.addEventListener('input', () => {
                saveIdentityToStorage();
                if (currentFileContent) {
                    fetchPreview();
                }
            });
        }
    });

    // File Drag & Drop
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

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    removeFileBtn.addEventListener('click', resetFile);

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
        fileInput.value = '';
        dropZone.style.display = 'block';
        fileInfo.style.display = 'none';
        exportPdfBtn.disabled = true;
        emptyState.style.display = 'flex';
        previewIframe.style.display = 'none';
        showStatus('');
    }

    // Load Demo Notebook
    loadDemoBtn.addEventListener('click', async () => {
        showStatus('Loading demo notebook...');
        try {
            const res = await fetch('/api/demo');
            if (!res.ok) throw new Error('Failed to load demo notebook');
            const data = await res.json();
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
            student_class: sClass
        };
    }

    // Fetch Live Preview
    async function fetchPreview() {
        if (!currentFileContent) return;
        showStatus('Rendering live preview with cover...');

        const payload = getPayloadData();

        try {
            const res = await fetch('/api/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Preview rendering failed');

            const htmlContent = await res.text();
            
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
            }, 100);

            showStatus('✨ Live Cover & Notebook Preview Ready!', 'green');
        } catch (err) {
            showStatus('❌ Preview error: ' + err.message, 'red');
        }
    }

    // Export PDF
    exportPdfBtn.addEventListener('click', async () => {
        if (!currentFileContent) return;

        exportPdfBtn.disabled = true;
        showStatus('⏳ Generating Colab PDF with Cover Header...');

        const payload = getPayloadData();

        try {
            const res = await fetch('/api/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                let errDetail = 'PDF conversion failed';
                try {
                    const errJson = await res.json();
                    if (errJson && errJson.error) errDetail = errJson.error;
                } catch (_) {}
                throw new Error(errDetail);
            }

            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = (currentFileName || 'notebook').replace('.ipynb', '') + '_report.pdf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);

            showStatus('🎉 PDF downloaded successfully!', 'green');
        } catch (err) {
            showStatus('❌ Conversion error: ' + err.message, 'red');
        } finally {
            exportPdfBtn.disabled = false;
        }
    });

    function showStatus(msg, color = 'black') {
        statusMsg.textContent = msg;
        statusMsg.style.color = color === 'green' ? '#008000' : color === 'red' ? '#CC0000' : '#000000';
    }
});

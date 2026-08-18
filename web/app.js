// OCH OCR v2 — Enterprise Document Intelligence Controller

const state = {
    activeDoc: "UU_Nomor_8_Tahun_1981.pdf",
    currentPage: 1,
    totalPages: 1,
    zoom: 1.0,
    rotation: 0,
    currentTheme: "sage",
    retrievalMode: "hybrid_rag",
    isProcessingOCR: false,
    isProcessingChat: false,
    inspectorOpen: false
};

// DOM Elements
const docSelect = document.getElementById("docSelect");
const fileUploadInput = document.getElementById("fileUploadInput");
const statusIndicator = document.getElementById("statusIndicator");
const statusText = document.getElementById("statusText");

// PDF Viewer DOM
const pageIndicator = document.getElementById("pageIndicator");
const btnPrevPage = document.getElementById("btnPrevPage");
const btnNextPage = document.getElementById("btnNextPage");
const btnZoomIn = document.getElementById("btnZoomIn");
const btnZoomOut = document.getElementById("btnZoomOut");
const zoomLevel = document.getElementById("zoomLevel");
const btnFitWidth = document.getElementById("btnFitWidth");
const btnFitPage = document.getElementById("btnFitPage");
const btnRotatePDF = document.getElementById("btnRotatePDF");
const btnDownloadPDF = document.getElementById("btnDownloadPDF");
const pdfViewport = document.getElementById("pdfViewport");
const pdfPageImage = document.getElementById("pdfPageImage");
const pdfPlaceholder = document.getElementById("pdfPlaceholder");
const pdfLoading = document.getElementById("pdfLoading");
const pdfHighlightOverlay = document.getElementById("pdfHighlightOverlay");

// Chat & Mode Selector DOM
const retrievalModeSelect = document.getElementById("retrievalModeSelect");
const chatConversationArea = document.getElementById("chatConversationArea");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const btnSendChat = document.getElementById("btnSendChat");

// Inspector DOM
const btnToggleInspector = document.getElementById("btnToggleInspector");
const inspectorDrawer = document.getElementById("inspectorDrawer");
const btnCloseInspector = document.getElementById("btnCloseInspector");
const inspectorJSONViewer = document.getElementById("inspectorJSONViewer");
const inspectorRawText = document.getElementById("inspectorRawText");
const rawCharStats = document.getElementById("rawCharStats");
const btnCopyJSON = document.getElementById("btnCopyJSON");
const btnCopyRaw = document.getElementById("btnCopyRaw");

// Theme Modal DOM
const themeModalBackdrop = document.getElementById("themeModalBackdrop");
const btnCloseThemeModal = document.getElementById("btnCloseThemeModal");
const btnSaveTheme = document.getElementById("btnSaveTheme");
const railTabSettings = document.getElementById("railTabSettings");
const btnUserMenu = document.getElementById("btnUserMenu");
const themeCards = document.querySelectorAll(".theme-card");

// Export DOM
const btnExport = document.getElementById("btnExport");
const btnExportJSON = document.getElementById("btnExportJSON");
const btnExportText = document.getElementById("btnExportText");
const btnExportMarkdown = document.getElementById("btnExportMarkdown");

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    initThemes();
    initAnalysisTabs();
    initInspectorTabs();
    initSafetyMonitor();
    initExportDropdown();
    loadDocumentList();
    initEventListeners();
});

// ==========================================================================
// THEME MANAGEMENT (PERSISTENT & INSTANT SWITCH)
// ==========================================================================
function initThemes() {
    const savedTheme = localStorage.getItem("och_theme") || "sage";
    applyTheme(savedTheme);

    themeCards.forEach(card => {
        card.addEventListener("click", () => {
            const chosen = card.getAttribute("data-theme-val");
            applyTheme(chosen);
        });
    });

    if (railTabSettings) {
        railTabSettings.addEventListener("click", () => {
            themeModalBackdrop.style.display = "flex";
        });
    }

    if (btnUserMenu) {
        btnUserMenu.addEventListener("click", () => {
            themeModalBackdrop.style.display = "flex";
        });
    }

    if (btnCloseThemeModal) {
        btnCloseThemeModal.addEventListener("click", () => {
            themeModalBackdrop.style.display = "none";
        });
    }

    if (btnSaveTheme) {
        btnSaveTheme.addEventListener("click", () => {
            themeModalBackdrop.style.display = "none";
        });
    }
}

function applyTheme(themeName) {
    state.currentTheme = themeName;
    document.documentElement.setAttribute("data-theme", themeName);
    localStorage.setItem("och_theme", themeName);

    themeCards.forEach(card => {
        if (card.getAttribute("data-theme-val") === themeName) {
            card.classList.add("active");
        } else {
            card.classList.remove("active");
        }
    });
}

// ==========================================================================
// EXPORT DROPDOWN
// ==========================================================================
function initExportDropdown() {
    if (btnExport) {
        const dropdownWrap = btnExport.closest(".dropdown");
        btnExport.addEventListener("click", (e) => {
            e.stopPropagation();
            if (dropdownWrap) dropdownWrap.classList.toggle("open");
        });

        document.addEventListener("click", (e) => {
            if (dropdownWrap && !dropdownWrap.contains(e.target)) {
                dropdownWrap.classList.remove("open");
            }
        });
    }

    if (btnExportJSON) {
        btnExportJSON.addEventListener("click", () => {
            const jsonText = inspectorJSONViewer.textContent;
            downloadBlob(jsonText, `${state.activeDoc}_analysis.json`, "application/json");
        });
    }

    if (btnExportText) {
        btnExportText.addEventListener("click", () => {
            const rawText = inspectorRawText.value || "Dokumen OCH OCR";
            downloadBlob(rawText, `${state.activeDoc}_raw.txt`, "text/plain");
        });
    }

    if (btnExportMarkdown) {
        btnExportMarkdown.addEventListener("click", () => {
            const md = `# Analisis Dokumen: ${state.activeDoc}\n\n## Hasil Analisis\n${document.getElementById("articleIntro")?.textContent || ''}\n`;
            downloadBlob(md, `${state.activeDoc}_report.md`, "text/markdown");
        });
    }
}

function downloadBlob(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ==========================================================================
// ANALYSIS & INSPECTOR TABS
// ==========================================================================
function initAnalysisTabs() {
    const atabs = document.querySelectorAll(".analysis-tab");
    atabs.forEach(tab => {
        tab.addEventListener("click", () => {
            atabs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".analysis-pane").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const targetId = `pane-${tab.getAttribute("data-atab")}`;
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add("active");

            const scrollArea = document.querySelector(".analysis-scroll-area");
            if (scrollArea) scrollArea.scrollTop = 0;
        });
    });
}

function initInspectorTabs() {
    const itbs = document.querySelectorAll(".itb");
    itbs.forEach(tab => {
        tab.addEventListener("click", () => {
            itbs.forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".itb-pane").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const targetId = tab.getAttribute("data-itb");
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add("active");
        });
    });

    if (btnToggleInspector) {
        btnToggleInspector.addEventListener("click", () => {
            state.inspectorOpen = !state.inspectorOpen;
            inspectorDrawer.classList.toggle("open", state.inspectorOpen);
        });
    }

    if (btnCloseInspector) {
        btnCloseInspector.addEventListener("click", () => {
            state.inspectorOpen = false;
            inspectorDrawer.classList.remove("open");
        });
    }

    if (btnCopyJSON) {
        btnCopyJSON.addEventListener("click", () => {
            navigator.clipboard.writeText(inspectorJSONViewer.textContent);
            btnCopyJSON.textContent = "✓ Copied!";
            setTimeout(() => btnCopyJSON.textContent = "📋 Copy JSON", 1500);
        });
    }

    if (btnCopyRaw) {
        btnCopyRaw.addEventListener("click", () => {
            navigator.clipboard.writeText(inspectorRawText.value);
            btnCopyRaw.textContent = "✓ Copied!";
            setTimeout(() => btnCopyRaw.textContent = "📋 Copy Raw", 1500);
        });
    }
}

// ==========================================================================
// DOCUMENT & PDF VIEWER CONTROLLER
// ==========================================================================
async function loadDocumentList(selectedFilename = null) {
    try {
        const res = await fetch("/api/documents");
        if (res.ok) {
            const docs = await res.json();
            docSelect.innerHTML = "";

            if (docs.length === 0) {
                const opt = document.createElement("option");
                opt.value = "";
                opt.textContent = "Belum ada dokumen";
                docSelect.appendChild(opt);
                return;
            }

            docs.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d.filename;
                opt.textContent = d.filename;
                if (selectedFilename && d.filename === selectedFilename) {
                    opt.selected = true;
                }
                docSelect.appendChild(opt);
            });

            const target = selectedFilename || (docs.find(d => d.filename.includes("1981")) || docs[0]).filename;
            selectDocument(target);
        }
    } catch (err) {
        console.error("Failed to load documents:", err);
    }
}

async function selectDocument(filename) {
    if (!filename) return;
    state.activeDoc = filename;
    state.currentPage = 1;
    docSelect.value = filename;

    try {
        const res = await fetch(`/api/documents/${encodeURIComponent(filename)}/meta`);
        if (res.ok) {
            const meta = await res.json();
            state.totalPages = meta.total_pages || 1;
        } else {
            state.totalPages = 1;
        }
    } catch (err) {
        state.totalPages = 1;
    }

    updatePageIndicator();
    renderCurrentPage();
    loadAnalysisSummary(filename);
}

function updatePageIndicator() {
    pageIndicator.textContent = `${state.currentPage} / ${state.totalPages}`;
    btnPrevPage.disabled = state.currentPage <= 1;
    btnNextPage.disabled = state.currentPage >= state.totalPages;
}

async function renderCurrentPage() {
    if (!state.activeDoc) return;

    pdfLoading.style.display = "flex";
    pdfPlaceholder.style.display = "none";
    pdfPageImage.style.display = "none";

    const timestamp = Date.now();
    const url = `/api/documents/${encodeURIComponent(state.activeDoc)}/page/${state.currentPage}/image?scale=1.8&t=${timestamp}`;

    pdfPageImage.src = url;
    pdfPageImage.onload = () => {
        pdfLoading.style.display = "none";
        pdfPageImage.style.display = "block";
        applyZoom();
    };

    pdfPageImage.onerror = () => {
        pdfLoading.style.display = "none";
        pdfPlaceholder.style.display = "flex";
    };
}

function applyZoom() {
    if (pdfPageImage) {
        pdfPageImage.style.transform = `scale(${state.zoom}) rotate(${state.rotation}deg)`;
        pdfPageImage.style.transformOrigin = "top center";
        zoomLevel.textContent = `${Math.round(state.zoom * 100)}%`;
    }
}

// Global function for citation clicks
window.jumpToPDFPage = function(pageNum, articleName) {
    if (pageNum >= 1 && pageNum <= state.totalPages) {
        state.currentPage = pageNum;
        updatePageIndicator();
        renderCurrentPage();

        if (pdfHighlightOverlay) {
            pdfHighlightOverlay.classList.add("active");
            setTimeout(() => pdfHighlightOverlay.classList.remove("active"), 2000);
        }

        if (pdfViewport) {
            pdfViewport.scrollTo({ top: 0, behavior: "smooth" });
        }
    }
};

// ==========================================================================
// ANALYSIS SUMMARY LOADER
// ==========================================================================
async function loadAnalysisSummary(filename) {
    const summaryDocType = document.getElementById("summaryDocType");
    const summaryTotalPages = document.getElementById("summaryTotalPages");

    if (summaryDocType) {
        summaryDocType.textContent = filename.replace(".pdf", "").replace(/_/g, " ");
    }
    if (summaryTotalPages) {
        summaryTotalPages.textContent = `${state.totalPages} Halaman`;
    }
}

// ==========================================================================
// CHAT & RETRIEVAL HANDLER
// ==========================================================================
async function handleSendChat(e) {
    if (e) e.preventDefault();
    const query = chatInput.value.trim();
    if (!query || state.isProcessingChat) return;

    appendUserBubble(query);
    chatInput.value = "";
    state.isProcessingChat = true;

    const loadingCardId = `load-${Date.now()}`;
    appendLoadingCard(loadingCardId);

    const mode = retrievalModeSelect ? retrievalModeSelect.value : "hybrid_rag";
    const llmModelSelect = document.getElementById("llmModelSelect");
    const chosenModel = llmModelSelect ? llmModelSelect.value : "qwen-35b";

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pdf_name: state.activeDoc,
                page_number: state.currentPage,
                messages: [{ role: "user", content: query }],
                retrieval_mode: mode,
                model: chosenModel
            })
        });


        const data = await res.json();
        removeLoadingCard(loadingCardId);

        if (res.ok) {
            appendAssistantCard(data.reply, data.citations || []);
            updateAnalysisPanel(query, data.reply, data.citations || []);
        } else {
            appendAssistantCard("Maaf, terjadi kendala saat memproses permintaan dokumen.", []);
        }
    } catch (err) {
        removeLoadingCard(loadingCardId);
        appendAssistantCard("Koneksi retrieval terputus. Silakan coba kembali.", []);
    } finally {
        state.isProcessingChat = false;
    }
}

function appendUserBubble(text) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble user-bubble";
    bubble.innerHTML = `
        <div class="bubble-text">${escapeHtml(text)}</div>
        <span class="bubble-time">${timeStr}</span>
    `;
    chatConversationArea.appendChild(bubble);
    chatConversationArea.scrollTop = chatConversationArea.scrollHeight;
}

function appendAssistantCard(replyText, citations) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const card = document.createElement("div");
    card.className = "chat-response-card";

    let sourcesHtml = "";
    if (citations && citations.length > 0) {
        sourcesHtml = `
            <div class="card-sources">
                <div class="sources-label">Sumber Dokumen</div>
                <div class="sources-list">
                    ${citations.slice(0, 4).map(c => `
                        <div class="source-item" onclick="jumpToPDFPage(${c.page_number}, '${escapeHtml(c.chunk_id)}')">
                            <div class="src-left">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                                <div class="src-info">
                                    <span class="src-title">${escapeHtml(c.section_title || 'Pasal Rujukan')}</span>
                                    <span class="src-sub">Halaman ${c.page_number}</span>
                                </div>
                            </div>
                            <span class="src-badge">${Math.round((c.score || 0.95) * 100)}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="card-header">
            <div class="card-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"></path></svg>
            </div>
            <span class="card-author">Jawaban</span>
            <span class="card-time">${timeStr}</span>
        </div>
        <div class="card-body">
            <p>${escapeHtml(replyText)}</p>
        </div>
        ${sourcesHtml}
    `;

    chatConversationArea.appendChild(card);
    chatConversationArea.scrollTop = chatConversationArea.scrollHeight;
}

function appendLoadingCard(id) {
    const card = document.createElement("div");
    card.id = id;
    card.className = "chat-response-card";
    card.innerHTML = `
        <div class="card-body" style="padding: 10px; color: var(--text-muted); display: flex; align-items: center; gap: 8px;">
            <div class="spinner-ring" style="width: 14px; height: 14px; border: 2px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
            <span>Menganalisis dokumen & sitasi hukum...</span>
        </div>
    `;
    chatConversationArea.appendChild(card);
    chatConversationArea.scrollTop = chatConversationArea.scrollHeight;
}

function removeLoadingCard(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function updateAnalysisPanel(query, answer, citations) {
    const articleTitle = document.getElementById("articleTitle");
    const articleIntro = document.getElementById("articleIntro");
    const citationCardsGrid = document.getElementById("citationCardsGrid");

    if (articleTitle) articleTitle.textContent = query;
    if (articleIntro) articleIntro.textContent = answer;

    if (citationCardsGrid && citations && citations.length > 0) {
        citationCardsGrid.innerHTML = citations.slice(0, 4).map(c => `
            <div class="citation-card" data-page="${c.page_number}">
                <div class="card-top">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    <span class="cit-name">${escapeHtml(c.section_title || 'Pasal ' + c.page_number)}</span>
                </div>
                <span class="cit-page">Halaman ${c.page_number}</span>
                <div class="cit-meta">
                    <span class="cit-relevance">Relevansi ${Math.round((c.score || 0.95) * 100)}%</span>
                    <button class="btn-jump-pdf" onclick="jumpToPDFPage(${c.page_number}, '${escapeHtml(c.chunk_id)}')">Lihat di PDF</button>
                </div>
            </div>
        `).join('');
    }

    const scrollArea = document.querySelector(".analysis-scroll-area");
    if (scrollArea) scrollArea.scrollTop = 0;
}

// ==========================================================================
// SAFETY STATUS POLLING (BACKGROUND)
// ==========================================================================
function initSafetyMonitor() {
    async function updateStatus() {
        try {
            const res = await fetch("/api/safety/status");
            if (res.ok) {
                const data = await res.json();
                if (data.limiter && statusText) {
                    statusText.textContent = data.limiter.ocr_ready ? "OCR Ready" : `Cooldown (${data.limiter.ocr_cooldown_remaining_seconds}s)`;
                }
            }
        } catch (err) {
            // Keep silent
        }
    }
    updateStatus();
    setInterval(updateStatus, 2500);
}

// ==========================================================================
// EVENT LISTENERS
// ==========================================================================
function initEventListeners() {
    docSelect.addEventListener("change", (e) => selectDocument(e.target.value));

    btnPrevPage.addEventListener("click", () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            updatePageIndicator();
            renderCurrentPage();
        }
    });

    btnNextPage.addEventListener("click", () => {
        if (state.currentPage < state.totalPages) {
            state.currentPage++;
            updatePageIndicator();
            renderCurrentPage();
        }
    });

    btnZoomIn.addEventListener("click", () => {
        state.zoom = Math.min(2.5, state.zoom + 0.15);
        applyZoom();
    });

    btnZoomOut.addEventListener("click", () => {
        state.zoom = Math.max(0.5, state.zoom - 0.15);
        applyZoom();
    });

    if (btnFitWidth) {
        btnFitWidth.addEventListener("click", () => {
            state.zoom = 1.0;
            state.rotation = 0;
            applyZoom();
        });
    }

    if (btnFitPage) {
        btnFitPage.addEventListener("click", () => {
            state.zoom = 0.85;
            applyZoom();
        });
    }

    if (btnRotatePDF) {
        btnRotatePDF.addEventListener("click", () => {
            state.rotation = (state.rotation + 90) % 360;
            applyZoom();
        });
    }

    if (btnDownloadPDF) {
        btnDownloadPDF.addEventListener("click", () => {
            window.open(`/api/documents/${encodeURIComponent(state.activeDoc)}/download`, '_blank');
        });
    }

    chatForm.addEventListener("submit", handleSendChat);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendChat();
        }
    });

    fileUploadInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            statusText.textContent = "Mengunggah...";
            const res = await fetch("/api/documents/upload", {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                loadDocumentList(data.file_name);
                statusText.textContent = "OCR Ready";
            }
        } catch (err) {
            statusText.textContent = "Upload Gagal";
        }
    });
}

function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

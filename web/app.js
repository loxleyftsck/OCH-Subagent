// OCH OCR v2 — Enterprise Document Intelligence Controller

const state = {
    activeDoc: "UU_Nomor_8_Tahun_1981.pdf",
    currentPage: 1,
    totalPages: 1,
    zoom: 1.0,
    rotation: 0,
    currentTheme: "sage",
    retrievalMode: "hybrid_rag",
    selectedText: "",
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
const pdfCanvasWrapper = document.getElementById("pdfCanvasWrapper");
const pdfPageImage = document.getElementById("pdfPageImage");
const pdfPlaceholder = document.getElementById("pdfPlaceholder");
const pdfLoading = document.getElementById("pdfLoading");
const pdfHighlightOverlay = document.getElementById("pdfHighlightOverlay");

// Selection Tooltip DOM
const selectionTooltip = document.getElementById("selectionTooltip");
const btnAskSelection = document.getElementById("btnAskSelection");
const btnSummarizeSelection = document.getElementById("btnSummarizeSelection");
const btnCopySelection = document.getElementById("btnCopySelection");

// Chat & Mode Selector DOM
const llmModelSelect = document.getElementById("llmModelSelect");
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
    initTextSelectionTooltip();
    loadDocumentList();
    initEventListeners();
    renderLegalKnowledgeGraph();
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
// TEXT SELECTION TOOLTIP (CONTEXTUAL "ASK AI" BAR)
// ==========================================================================
function initTextSelectionTooltip() {
    if (!pdfCanvasWrapper || !selectionTooltip) return;

    pdfViewport.addEventListener("mouseup", (e) => {
        const sel = window.getSelection();
        const text = sel.toString().trim();
        if (text && text.length > 2) {
            state.selectedText = text;
            const rect = sel.getRangeAt(0).getBoundingClientRect();
            const parentRect = pdfViewport.getBoundingClientRect();
            
            selectionTooltip.style.top = `${rect.top - parentRect.top - 42}px`;
            selectionTooltip.style.left = `${Math.max(10, rect.left - parentRect.left + (rect.width / 2) - 120)}px`;
            selectionTooltip.style.display = "flex";
        } else {
            selectionTooltip.style.display = "none";
        }
    });

    document.addEventListener("mousedown", (e) => {
        if (selectionTooltip && !selectionTooltip.contains(e.target) && !pdfViewport.contains(e.target)) {
            selectionTooltip.style.display = "none";
        }
    });

    if (btnAskSelection) {
        btnAskSelection.addEventListener("click", () => {
            selectionTooltip.style.display = "none";
            const q = `Jelaskan maksud dari bagian ini: "${state.selectedText}"`;
            chatInput.value = q;
            handleSendChat();
        });
    }

    if (btnSummarizeSelection) {
        btnSummarizeSelection.addEventListener("click", () => {
            selectionTooltip.style.display = "none";
            const q = `Ringkas pokok hukum berikut: "${state.selectedText}"`;
            chatInput.value = q;
            handleSendChat();
        });
    }

    if (btnCopySelection) {
        btnCopySelection.addEventListener("click", () => {
            navigator.clipboard.writeText(state.selectedText);
            selectionTooltip.style.display = "none";
        });
    }
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

            if (tab.getAttribute("data-atab") === "graf") {
                renderLegalKnowledgeGraph();
            }
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
            btnCopyJSON.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"></polyline></svg> <span>Tersalin</span>`;
            setTimeout(() => {
                btnCopyJSON.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> <span>Copy JSON</span>`;
            }, 1500);
        });
    }

    if (btnCopyRaw) {
        btnCopyRaw.addEventListener("click", () => {
            navigator.clipboard.writeText(inspectorRawText.value);
            btnCopyRaw.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><polyline points="20 6 9 17 4 12"></polyline></svg> <span>Tersalin</span>`;
            setTimeout(() => {
                btnCopyRaw.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> <span>Copy Raw</span>`;
            }, 1500);
        });
    }
}

// ==========================================================================
// INTERACTIVE LEGAL KNOWLEDGE GRAPH RENDERER
// ==========================================================================
function renderLegalKnowledgeGraph() {
    const svg = document.getElementById("legalGraphSvg");
    if (!svg) return;

    svg.innerHTML = `
        <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#84968C" />
            </marker>
        </defs>
        
        <!-- Links -->
        <g stroke="#D8E2DA" stroke-width="1.5" marker-end="url(#arrow)">
            <line x1="270" y1="50" x2="160" y2="140" />
            <line x1="270" y1="50" x2="380" y2="140" />
            <line x1="160" y1="140" x2="90" y2="230" />
            <line x1="160" y1="140" x2="230" y2="230" />
            <line x1="380" y1="140" x2="450" y2="230" />
        </g>

        <!-- Relation Labels -->
        <g font-size="9" fill="#53645A" text-anchor="middle" font-weight="500">
            <text x="205" y="90">berdasar</text>
            <text x="335" y="90">mengatur</text>
            <text x="115" y="180">rujukan</text>
            <text x="205" y="180">turunan</text>
            <text x="425" y="180">kontrol</text>
        </g>

        <!-- Nodes (Interactive Click to Page Jump) -->
        <!-- Root Node: UU 8/1981 -->
        <g class="graph-node" onclick="jumpToPDFPage(1, 'UU 8/1981')" style="cursor: pointer;">
            <circle cx="270" cy="50" r="24" fill="var(--primary)" filter="drop-shadow(0 2px 4px rgba(0,0,0,0.1))" />
            <text x="270" y="53" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">UU 8/1981</text>
        </g>

        <!-- Node: Pasal 9 -->
        <g class="graph-node" onclick="jumpToPDFPage(3, 'Pasal 9')" style="cursor: pointer;">
            <circle cx="160" cy="140" r="20" fill="var(--primary)" />
            <text x="160" y="143" font-size="9.5" font-weight="600" fill="#FFFFFF" text-anchor="middle">Pasal 9</text>
            <text x="160" y="172" font-size="9" fill="var(--text-muted)" text-anchor="middle">Asas Bebas & Jujur</text>
        </g>

        <!-- Node: Pasal 10 -->
        <g class="graph-node" onclick="jumpToPDFPage(3, 'Pasal 10')" style="cursor: pointer;">
            <circle cx="380" cy="140" r="20" fill="var(--primary)" />
            <text x="380" y="143" font-size="9.5" font-weight="600" fill="#FFFFFF" text-anchor="middle">Pasal 10</text>
            <text x="380" y="172" font-size="9" fill="var(--text-muted)" text-anchor="middle">Praperadilan</text>
        </g>

        <!-- Sub Node: Pasal 12 -->
        <g class="graph-node" onclick="jumpToPDFPage(4, 'Pasal 12')" style="cursor: pointer;">
            <circle cx="90" cy="230" r="17" fill="#5E9D7A" />
            <text x="90" y="233" font-size="9" font-weight="600" fill="#FFFFFF" text-anchor="middle">Pasal 12</text>
        </g>

        <!-- Sub Node: Pasal 16 -->
        <g class="graph-node" onclick="jumpToPDFPage(4, 'Pasal 16')" style="cursor: pointer;">
            <circle cx="230" cy="230" r="17" fill="#5E9D7A" />
            <text x="230" y="233" font-size="9" font-weight="600" fill="#FFFFFF" text-anchor="middle">Pasal 16</text>
        </g>

        <!-- Sub Node: Pasal 77 -->
        <g class="graph-node" onclick="jumpToPDFPage(12, 'Pasal 77')" style="cursor: pointer;">
            <circle cx="450" cy="230" r="17" fill="#5E9D7A" />
            <text x="450" y="233" font-size="9" font-weight="600" fill="#FFFFFF" text-anchor="middle">Pasal 77</text>
        </g>
    `;
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
            setTimeout(() => pdfHighlightOverlay.classList.remove("active"), 2200);
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
// SSE REAL-TIME STREAMING CHAT HANDLER
// ==========================================================================
async function handleSendChat(e) {
    if (e) e.preventDefault();
    const query = chatInput.value.trim();
    if (!query || state.isProcessingChat) return;

    appendUserBubble(query);
    chatInput.value = "";
    state.isProcessingChat = true;

    const cardId = `msg-${Date.now()}`;
    const cardEl = appendStreamingCard(cardId);
    const bodyParagraph = cardEl.querySelector(".stream-text");

    const mode = retrievalModeSelect ? retrievalModeSelect.value : "hybrid_rag";
    const chosenModel = llmModelSelect ? llmModelSelect.value : "qwen-35b";

    let fullAnswer = "";
    let capturedCitations = [];

    try {
        const response = await fetch("/api/chat/stream", {
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

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const jsonStr = line.replace("data: ", "").trim();
                    if (!jsonStr) continue;
                    try {
                        const payload = JSON.parse(jsonStr);
                        if (payload.type === "token") {
                            fullAnswer += payload.token;
                            bodyParagraph.textContent = fullAnswer;
                            chatConversationArea.scrollTop = chatConversationArea.scrollHeight;
                        } else if (payload.type === "citations") {
                            capturedCitations = payload.citations || [];
                            attachCitationsToCard(cardEl, capturedCitations);
                        } else if (payload.type === "done") {
                            updateAnalysisPanel(query, fullAnswer, capturedCitations);
                        }
                    } catch (pe) {
                        // ignore malformed JSON chunk
                    }
                }
            }
        }
    } catch (err) {
        bodyParagraph.textContent = "Koneksi retrieval terputus atau offline. Silakan coba kembali.";
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

function appendStreamingCard(id) {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const card = document.createElement("div");
    card.id = id;
    card.className = "chat-response-card";

    card.innerHTML = `
        <div class="card-header">
            <div class="card-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"></path></svg>
            </div>
            <span class="card-author">Jawaban</span>
            <span class="card-time">${timeStr}</span>
        </div>
        <div class="card-body">
            <p class="stream-text" style="white-space: pre-wrap;"></p>
        </div>
        <div class="sources-placeholder"></div>
    `;

    chatConversationArea.appendChild(card);
    chatConversationArea.scrollTop = chatConversationArea.scrollHeight;
    return card;
}

function attachCitationsToCard(cardEl, citations) {
    const placeholder = cardEl.querySelector(".sources-placeholder");
    if (!placeholder || !citations || citations.length === 0) return;

    placeholder.innerHTML = `
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

function updateAnalysisPanel(query, answer, citations) {
    const articleTitle = document.getElementById("articleTitle");
    const articleIntro = document.getElementById("articleIntro");
    const citationCardsGrid = document.getElementById("citationCardsGrid");

    if (articleTitle) articleTitle.textContent = query;
    if (articleIntro) articleIntro.textContent = answer;

    if (citationCardsGrid && citations && citations.length > 0) {
        citationCardsGrid.innerHTML = citations.slice(0, 4).map(c => `
            <div class="citation-card" data-page="${c.page_number}">
                <div>
                    <div class="card-top">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                        <span class="cit-name">${escapeHtml(c.section_title || 'Pasal ' + c.page_number)}</span>
                    </div>
                    <span class="cit-page">Halaman ${c.page_number}</span>
                </div>
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

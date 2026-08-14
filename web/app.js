// OCH-Subagent Web Dashboard Controller

const state = {
    activeDoc: null,
    currentPage: 1,
    totalPages: 1,
    zoom: 1.0,
    chatMessages: [],
    ocrResult: null,
    isProcessingOCR: false,
    isProcessingChat: false
};

// DOM Elements
const docSelect = document.getElementById("docSelect");
const btnDownloadHF = document.getElementById("btnDownloadHF");
const fileUploadInput = document.getElementById("fileUploadInput");

const pageIndicator = document.getElementById("pageIndicator");
const btnPrevPage = document.getElementById("btnPrevPage");
const btnNextPage = document.getElementById("btnNextPage");
const btnZoomIn = document.getElementById("btnZoomIn");
const btnZoomOut = document.getElementById("btnZoomOut");
const zoomLevel = document.getElementById("zoomLevel");

const pdfCanvasContainer = document.getElementById("pdfCanvasContainer");
const pdfPageImage = document.getElementById("pdfPageImage");
const pdfPlaceholder = document.getElementById("pdfPlaceholder");
const pdfLoading = document.getElementById("pdfLoading");
const pdfLoadingText = document.getElementById("pdfLoadingText");

const btnRunOCR = document.getElementById("btnRunOCR");
const ocrCacheBadge = document.getElementById("ocrCacheBadge");

const structuredView = document.getElementById("structuredView");
const rawTextOutput = document.getElementById("rawTextOutput");
const rawStats = document.getElementById("rawStats");
const btnCopyRaw = document.getElementById("btnCopyRaw");

const metaModel = document.getElementById("metaModel");
const metaHash = document.getElementById("metaHash");
const metaCacheStatus = document.getElementById("metaCacheStatus");
const metaTokens = document.getElementById("metaTokens");

const ocrCooldownBadge = document.getElementById("ocrCooldownBadge");
const slotBadge = document.getElementById("slotBadge");
const dailyUsageBadge = document.getElementById("dailyUsageBadge");

const chatModelSelect = document.getElementById("chatModelSelect");
const chatMessagesContainer = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const btnSendChat = document.getElementById("btnSendChat");

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initSafetyMonitor();
    loadDocumentList();
    initEventListeners();
});

// --- TABS CONTROLLER ---
function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add("active");
        });
    });
}

// --- REAL-TIME SAFETY & QUOTA MONITOR ---
function initSafetyMonitor() {
    async function updateStatus() {
        try {
            const res = await fetch("/api/safety/status");
            if (res.ok) {
                const data = await res.json();
                const limiter = data.limiter;
                const quota = data.quota;

                // Cooldown badge
                if (limiter.ocr_ready) {
                    ocrCooldownBadge.textContent = "Ready 🟢";
                    ocrCooldownBadge.style.color = "#10B981";
                } else {
                    ocrCooldownBadge.textContent = `Cooldown: ${limiter.ocr_cooldown_remaining_seconds}s ⏳`;
                    ocrCooldownBadge.style.color = "#F59E0B";
                }

                // Slot badge
                slotBadge.textContent = `${limiter.active_concurrency} / ${limiter.max_concurrency} Active`;
                
                // Usage badge
                dailyUsageBadge.textContent = `${quota.ocr_calls} / ${quota.max_daily_ocr_calls} Calls`;
            }
        } catch (err) {
            console.warn("Safety status polling error:", err);
        }
    }

    updateStatus();
    setInterval(updateStatus, 1500);
}

// --- DOCUMENT MANAGEMENT ---
async function loadDocumentList(selectedFilename = null) {
    try {
        const res = await fetch("/api/documents");
        if (res.ok) {
            const docs = await res.json();
            docSelect.innerHTML = "";

            if (docs.length === 0) {
                const opt = document.createElement("option");
                opt.value = "";
                opt.textContent = "Belum ada dokumen (Download HF / Upload)";
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

            // Automatically select first or requested
            const target = selectedFilename || docs[0].filename;
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
    state.zoom = 1.0;
    zoomLevel.textContent = "100%";

    try {
        const res = await fetch(`/api/documents/${filename}/meta`);
        if (res.ok) {
            const meta = await res.json();
            state.totalPages = meta.total_pages;
            updatePageIndicator();
            renderActivePage();
        }
    } catch (err) {
        console.error("Error fetching doc meta:", err);
    }
}

function updatePageIndicator() {
    pageIndicator.textContent = `Page ${state.currentPage} / ${state.totalPages}`;
    btnPrevPage.disabled = state.currentPage <= 1;
    btnNextPage.disabled = state.currentPage >= state.totalPages;
}

function renderActivePage() {
    if (!state.activeDoc) return;

    pdfLoadingText.textContent = `Rendering Page ${state.currentPage}...`;
    pdfLoading.style.display = "flex";
    pdfPlaceholder.style.display = "none";

    const imgUrl = `/api/documents/${state.activeDoc}/page/${state.currentPage}/image?scale=1.6&t=${Date.now()}`;
    pdfPageImage.src = imgUrl;

    pdfPageImage.onload = () => {
        pdfLoading.style.display = "none";
        pdfPageImage.style.display = "block";
        applyZoom();
    };

    pdfPageImage.onerror = () => {
        pdfLoading.style.display = "none";
        alert("Gagal merender halaman dokumen.");
    };
}

function applyZoom() {
    pdfPageImage.style.transform = "none";
    pdfPageImage.style.width = `${Math.round(state.zoom * 95)}%`;
    pdfPageImage.style.maxWidth = state.zoom > 1.0 ? "none" : "95%";
    zoomLevel.textContent = `${Math.round(state.zoom * 100)}%`;
}


// --- EVENT LISTENERS ---
function initEventListeners() {
    docSelect.addEventListener("change", (e) => {
        selectDocument(e.target.value);
    });

    btnPrevPage.addEventListener("click", () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            updatePageIndicator();
            renderActivePage();
        }
    });

    btnNextPage.addEventListener("click", () => {
        if (state.currentPage < state.totalPages) {
            state.currentPage++;
            updatePageIndicator();
            renderActivePage();
        }
    });

    btnZoomIn.addEventListener("click", () => {
        if (state.zoom < 2.5) {
            state.zoom += 0.15;
            applyZoom();
        }
    });

    btnZoomOut.addEventListener("click", () => {
        if (state.zoom > 0.5) {
            state.zoom -= 0.15;
            applyZoom();
        }
    });

    // HF Download Button
    btnDownloadHF.addEventListener("click", async () => {
        btnDownloadHF.disabled = true;
        btnDownloadHF.textContent = "⏳ Downloading HF Row 4...";
        try {
            const formData = new FormData();
            formData.append("row_index", "4");
            const res = await fetch("/api/documents/download-hf", {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                await loadDocumentList(data.file_name);
                alert(`✅ Berhasil mengunduh dokumen: ${data.file_name}`);
            } else {
                const errData = await res.json();
                alert(`Gagal download: ${errData.detail}`);
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            btnDownloadHF.disabled = false;
            btnDownloadHF.textContent = "📥 Download HF Row 4";
        }
    });

    // File Upload
    fileUploadInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/api/documents/upload", {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                await loadDocumentList(data.file_name);
                alert(`✅ File berhasil diunggah: ${data.file_name}`);
            }
        } catch (err) {
            alert(`Gagal upload: ${err.message}`);
        }
    });

    // OCR Button
    btnRunOCR.addEventListener("click", executeOCR);

    // Copy Raw Text
    btnCopyRaw.addEventListener("click", () => {
        if (rawTextOutput.value) {
            navigator.clipboard.writeText(rawTextOutput.value);
            btnCopyRaw.textContent = "✅ Copied!";
            setTimeout(() => { btnCopyRaw.textContent = "📋 Copy Text"; }, 2000);
        }
    });

    // Chat Form Submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendChatMessage();
    });

    // Quick Prompts
    document.querySelectorAll(".quick-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            chatInput.value = btn.getAttribute("data-prompt");
            chatInput.focus();
        });
    });
}

// --- OCR PIPELINE EXECUTION ---
async function executeOCR() {
    if (!state.activeDoc) {
        alert("Silakan pilih dokumen terlebih dahulu.");
        return;
    }
    if (state.isProcessingOCR) return;

    state.isProcessingOCR = true;
    btnRunOCR.disabled = true;
    btnRunOCR.innerHTML = "⏳ Menjalankan Subagents...";

    try {
        const formData = new FormData();
        formData.append("page_number", state.currentPage.toString());
        formData.append("auto_structure", "true");

        const res = await fetch(`/api/documents/${state.activeDoc}/ocr`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Gagal memproses OCR");
        }

        const data = await res.json();
        state.ocrResult = data;
        displayOCRResult(data);

    } catch (err) {
        alert(`OCR Error: ${err.message}`);
    } finally {
        state.isProcessingOCR = false;
        btnRunOCR.disabled = false;
        btnRunOCR.innerHTML = "⚡ Ekstrak OCR";
    }
}

function displayOCRResult(data) {
    // 1. Raw text tab
    rawTextOutput.value = data.raw_text || "";
    const lines = (data.raw_text || "").split("\n").length;
    const chars = (data.raw_text || "").length;
    rawStats.textContent = `${chars} Karakter | ${lines} Baris`;

    // 2. Structured JSON tab
    if (data.structured_data) {
        const s = data.structured_data;
        
        // Check if receipt schema or general document
        const isReceipt = s.document_type && (
            s.document_type.toLowerCase().includes("struk") || 
            s.document_type.toLowerCase().includes("receipt") || 
            s.merchant_name || 
            (s.items && s.items.length > 0)
        );

        if (isReceipt) {
            let itemsHtml = "";
            if (s.items && s.items.length > 0) {
                itemsHtml = `
                <div class="receipt-items-table-wrapper">
                    <table class="receipt-table">
                        <thead>
                            <tr>
                                <th>Item / Produk</th>
                                <th style="text-align:center;">Qty</th>
                                <th style="text-align:right;">Harga</th>
                                <th style="text-align:right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${s.items.map(it => `
                                <tr>
                                    <td><strong>${it.name || "-"}</strong></td>
                                    <td style="text-align:center;">${it.qty || 1}</td>
                                    <td style="text-align:right;">${it.unit_price ? Number(it.unit_price).toLocaleString('id-ID') : '-'}</td>
                                    <td style="text-align:right; font-weight:600;">${it.total_price ? Number(it.total_price).toLocaleString('id-ID') : '-'}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>`;
            }

            structuredView.innerHTML = `
                <div class="structured-card receipt-card">
                    <div class="receipt-header-badge">🧾 STRUK / RECEIPT DETECTED</div>
                    <div class="struct-row">
                        <span class="struct-key">Merchant / Toko</span>
                        <span class="struct-val" style="font-size:1.1rem; font-weight:700; color:#38BDF8;">${s.merchant_name || s.document_title || "Struk Belanja"}</span>
                    </div>
                    <div class="receipt-meta-grid">
                        ${s.receipt_number ? `<div><span class="struct-key">No. Struk:</span> <span class="struct-val font-mono">${s.receipt_number}</span></div>` : ""}
                        ${s.transaction_date ? `<div><span class="struct-key">Tanggal:</span> <span class="struct-val">${s.transaction_date} ${s.transaction_time || ""}</span></div>` : ""}
                        ${s.cashier ? `<div><span class="struct-key">Kasir:</span> <span class="struct-val">${s.cashier}</span></div>` : ""}
                    </div>
                    
                    ${itemsHtml}

                    <div class="receipt-totals-box">
                        ${s.subtotal ? `<div class="total-row"><span>Subtotal:</span><span>Rp ${Number(s.subtotal).toLocaleString('id-ID')}</span></div>` : ""}
                        ${s.discount ? `<div class="total-row discount"><span>Diskon:</span><span>-Rp ${Number(s.discount).toLocaleString('id-ID')}</span></div>` : ""}
                        ${s.tax ? `<div class="total-row"><span>PPN / Pajak:</span><span>Rp ${Number(s.tax).toLocaleString('id-ID')}</span></div>` : ""}
                        <div class="total-row grand-total">
                            <span>TOTAL BAYAR:</span>
                            <span class="total-amount">${s.total_amount ? `Rp ${Number(s.total_amount).toLocaleString('id-ID')}` : "-"}</span>
                        </div>
                        ${s.payment_method ? `<div class="total-row payment-method"><span>Metode Bayar:</span><span class="badge badge-slot">${s.payment_method}</span></div>` : ""}
                        ${s.change_amount ? `<div class="total-row"><span>Kembalian:</span><span>Rp ${Number(s.change_amount).toLocaleString('id-ID')}</span></div>` : ""}
                    </div>

                    ${s.summary ? `
                    <div class="struct-row" style="margin-top:12px;">
                        <span class="struct-key">Ringkasan</span>
                        <div class="struct-summary">${s.summary}</div>
                    </div>` : ""}
                </div>
            `;
        } else {
            // General Document Schema
            structuredView.innerHTML = `
                <div class="structured-card">
                    <div class="struct-row">
                        <span class="struct-key">Judul Dokumen</span>
                        <span class="struct-val" style="font-weight:700; color: #6366F1;">${s.document_title || "-"}</span>
                    </div>
                    <div class="struct-row">
                        <span class="struct-key">Tipe Dokumen</span>
                        <span class="struct-val">${s.document_type || "Generic"}</span>
                    </div>
                    ${s.reference_number ? `
                    <div class="struct-row">
                        <span class="struct-key">Nomor Referensi</span>
                        <span class="struct-val" style="font-family: monospace; color:#38BDF8;">${s.reference_number}</span>
                    </div>` : ""}
                    ${s.dates && s.dates.length ? `
                    <div class="struct-row">
                        <span class="struct-key">Tanggal Terdeteksi</span>
                        <span class="struct-val">${Array.isArray(s.dates) ? s.dates.join(", ") : s.dates}</span>
                    </div>` : ""}
                    ${s.organizations && s.organizations.length ? `
                    <div class="struct-row">
                        <span class="struct-key">Instansi / Organisasi</span>
                        <span class="struct-val">${Array.isArray(s.organizations) ? s.organizations.join(", ") : s.organizations}</span>
                    </div>` : ""}
                    <div class="struct-row">
                        <span class="struct-key">Ringkasan Eksekutif</span>
                        <div class="struct-summary">${s.summary || "-"}</div>
                    </div>
                </div>
                ${s.key_entities && Object.keys(s.key_entities).length ? `
                <div class="structured-card">
                    <span class="struct-key" style="margin-bottom:8px; display:block;">Entitas & Atribut Kunci</span>
                    <pre style="font-size:0.78rem; font-family:'JetBrains Mono',monospace; color:#A5B4FC; background:rgba(0,0,0,0.3); padding:10px; border-radius:6px; overflow-x:auto;">${JSON.stringify(s.key_entities, null, 2)}</pre>
                </div>` : ""}
            `;
        }
    } else {
        structuredView.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📝</span>
                <p>Teks mentah berhasil diekstrak. Lihat di tab <strong>Raw OCR Text</strong>.</p>
            </div>
        `;
    }

    // 3. Cache & Meta tab
    if (data.is_cached) {
        ocrCacheBadge.style.display = "inline-block";
        ocrCacheBadge.textContent = "⚡ Local Cache (0 Token Cost)";
        metaCacheStatus.textContent = "⚡ Cache Hit (Tanpa panggil API)";
        metaCacheStatus.style.color = "#10B981";
    } else {
        ocrCacheBadge.style.display = "inline-block";
        ocrCacheBadge.textContent = "🌐 Live API Call";
        ocrCacheBadge.style.background = "rgba(99, 102, 241, 0.2)";
        ocrCacheBadge.style.color = "#A5B4FC";
        metaCacheStatus.textContent = "🌐 Fresh API Call";
        metaCacheStatus.style.color = "#A5B4FC";
    }

    metaModel.textContent = data.model_name || "ocr-lighton";
    metaHash.textContent = data.image_hash || "-";
    metaTokens.textContent = `${data.token_estimate || 0} Tokens`;
}


// --- INTERACTIVE SUBAGENT CHAT ---
async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text || state.isProcessingChat) return;

    if (!state.activeDoc) {
        alert("Pilih dokumen terlebih dahulu sebelum memulai chat.");
        return;
    }

    state.isProcessingChat = true;
    chatInput.value = "";
    btnSendChat.disabled = true;

    // Append User Bubble
    appendChatMessage("user", text);
    state.chatMessages.push({ role: "user", content: text });

    // Append Loading Assistant Bubble
    const assistantBubbleId = `msg-asst-${Date.now()}`;
    appendChatMessage("assistant", "⏳ Subagent sedang menganalisis dokumen...", assistantBubbleId);

    try {
        const payload = {
            pdf_name: state.activeDoc,
            page_number: state.currentPage,
            messages: state.chatMessages,
            model: chatModelSelect.value
        };

        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Gagal memproses jawaban subagent");
        }

        const data = await res.json();
        updateAssistantMessage(assistantBubbleId, data.reply, data.model_used);
        state.chatMessages.push({ role: "assistant", content: data.reply });

    } catch (err) {
        updateAssistantMessage(assistantBubbleId, `⚠️ Terjadi kendala: ${err.message}`);
    } finally {
        state.isProcessingChat = false;
        btnSendChat.disabled = false;
    }
}

function appendChatMessage(role, content, bubbleId = null) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message message-${role}`;
    if (bubbleId) msgDiv.id = bubbleId;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = content;

    msgDiv.appendChild(bubble);
    chatMessagesContainer.appendChild(msgDiv);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function updateAssistantMessage(bubbleId, text, modelUsed = null) {
    const msgDiv = document.getElementById(bubbleId);
    if (msgDiv) {
        const bubble = msgDiv.querySelector(".message-bubble");
        if (bubble) {
            bubble.textContent = text;
            if (modelUsed) {
                const metaSpan = document.createElement("div");
                metaSpan.style.fontSize = "0.68rem";
                metaSpan.style.color = "#64748B";
                metaSpan.style.marginTop = "6px";
                metaSpan.textContent = `🤖 Answered by ${modelUsed}`;
                bubble.appendChild(metaSpan);
            }
        }
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }
}

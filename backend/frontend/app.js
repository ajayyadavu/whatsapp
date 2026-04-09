// app.js — FIXED: session_id is permanent per browser, never regenerated
// Greeting fires ONCE because session_id never changes across page reloads

// const BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    // ? "http://127.0.0.1:8000"
    // : "https://rag.gignaati.com:2019";

// const BASE_URL = "https://sophie-depletive-vulgarly.ngrok-free.dev";

// const API_CHAT = `${BASE_URL}/api/v1/chat/`;
// const API_LEAD = `${BASE_URL}/api/v1/lead/`;



const BASE_URL = "http://localhost:8000";

const API_CHAT = `${BASE_URL}/api/v1/chat/`;
const API_LEAD = `${BASE_URL}/api/v1/lead/`;


// ── PERMANENT session_id — never changes across page reloads ──────────────────
// KEY FIX: use a dedicated key "permanent_session_id" that is NEVER overwritten
// Old code used Date.now() which created a new session_id on every reload
const sessionId = (function () {
    const KEY = "swaran_session_id";
    let id = localStorage.getItem(KEY);
    if (!id) {
        id = "sess_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2);
        localStorage.setItem(KEY, id);
    }
    return id;
})();

const urlParams   = new URLSearchParams(window.location.search);
const utmSource   = urlParams.get("utm_source")   || "";
const utmMedium   = urlParams.get("utm_medium")   || "";
const utmCampaign = urlParams.get("utm_campaign") || "";

let chats           = {};
let currentChat     = null;
let messageCount    = 0;
let detectedSignals = [];
let leadFormShown   = false;

// ── Active request controller ──────────────────────────────────────────────────
let activeController = null;
let activeReader     = null;

function cancelActiveRequest() {
    if (activeReader)     { try { activeReader.cancel(); }     catch (_) {} activeReader = null; }
    if (activeController) { activeController.abort(); activeController = null; }
}

// ── Throttled scroll ───────────────────────────────────────────────────────────
let _scrollTimer = null;
function scheduleScroll(el) {
    if (_scrollTimer) return;
    _scrollTimer = setTimeout(() => {
        el.scrollTop = el.scrollHeight;
        _scrollTimer = null;
    }, 150);
}

// ─── Chat logic ────────────────────────────────────────────────────────────────

function newChat() {
    // NOTE: newChat() does NOT generate a new session_id — the backend session
    // (name, greeted flag, memory) is tied to the permanent sessionId above.
    // newChat() only clears the LOCAL chat display for a fresh UI conversation.
    cancelActiveRequest();
    const id = Date.now().toString();
    chats[id]       = [];
    currentChat     = id;
    messageCount    = 0;
    leadFormShown   = false;
    detectedSignals = [];
    renderHistory();
    renderChat();
}

async function sendMessage() {
    const input   = document.getElementById("input");
    const chatBox = document.getElementById("chat");
    const msg     = input.value.trim();

    if (!msg) return;
    if (!currentChat) newChat();

    cancelActiveRequest();

    chats[currentChat].push({ role: "user", text: msg });
    input.value = "";
    messageCount++;
    renderChat();

    const botDiv     = document.createElement("div");
    botDiv.className = "message bot thinking";
    botDiv.innerText = "Thinking…";
    chatBox.appendChild(botDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    const controller = new AbortController();
    activeController = controller;

    try {
        const response = await fetch(API_CHAT, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            // Always sends the same permanent sessionId — backend remembers state
            body:    JSON.stringify({ message: msg, session_id: sessionId }),
            signal:  controller.signal,
        });

        if (!response.ok) {
            botDiv.innerText = `Server error: ${response.status}`;
            botDiv.classList.remove("thinking");
            return;
        }

        const reader  = response.body.getReader();
        activeReader  = reader;
        const decoder = new TextDecoder("utf-8");

        let fullText    = "";
        let firstToken  = true;
        let rawBuffer   = "";
        let signalsDone = false;

        while (true) {
            let done, value;
            try {
                ({ done, value } = await reader.read());
            } catch (readErr) {
                if (readErr.name === "AbortError") break;
                throw readErr;
            }
            if (done) break;

            rawBuffer += decoder.decode(value, { stream: true });

            // ── Strip __SIGNALS__ header ───────────────────────────────────────
            if (!signalsDone) {
                const S  = "__SIGNALS__";
                const s1 = rawBuffer.indexOf(S);
                if (s1 !== -1) {
                    const s2 = rawBuffer.indexOf(S, s1 + S.length);
                    if (s2 !== -1) {
                        try { detectedSignals = JSON.parse(rawBuffer.slice(s1 + S.length, s2)); }
                        catch (_) { detectedSignals = []; }
                        rawBuffer   = rawBuffer.slice(s2 + S.length);
                        signalsDone = true;
                    }
                } else {
                    signalsDone = true;
                }
            }

            // ── Flush display text ─────────────────────────────────────────────
            if (signalsDone && rawBuffer) {
                if (firstToken) {
                    botDiv.innerText = "";
                    botDiv.classList.remove("thinking");
                    firstToken = false;
                }
                botDiv.insertAdjacentText("beforeend", rawBuffer);
                fullText  += rawBuffer;
                rawBuffer  = "";
                scheduleScroll(chatBox);
            }
        }

        if (!fullText.trim()) {
            botDiv.innerText = "No response received.";
            botDiv.classList.remove("thinking");
        }

        chats[currentChat].push({ role: "bot", text: fullText });
        renderHistory();

        if (!leadFormShown && (detectedSignals.length > 0 || messageCount >= 3)) {
            showLeadBanner();
        }

    } catch (err) {
        if (err.name === "AbortError") {
            if (botDiv.parentNode) botDiv.parentNode.removeChild(botDiv);
        } else {
            console.error("Fetch error:", err);
            botDiv.innerText = "Error: Could not reach the backend.";
            botDiv.classList.remove("thinking");
        }
    } finally {
        if (activeController === controller) {
            activeController = null;
            activeReader     = null;
        }
    }
}

// ─── Lead capture ──────────────────────────────────────────────────────────────

function showLeadBanner() {
    if (leadFormShown) return;
    leadFormShown = true;
    const chatBox = document.getElementById("chat");
    const banner  = document.createElement("div");
    banner.className = "lead-banner";
    banner.innerHTML = `
        <div>
            <strong>Want a personalised demo?</strong>
            <span style="display:block;font-size:13px;opacity:0.8">Our team can walk you through a live pilot.</span>
        </div>
        <button onclick="showLeadForm()">Book a Demo →</button>`;
    chatBox.appendChild(banner);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showLeadForm()  { document.getElementById("lead-modal").style.display = "flex"; }
function closeLeadForm() { document.getElementById("lead-modal").style.display = "none"; }

async function submitLead() {
    const name     = document.getElementById("lead-name").value.trim();
    const email    = document.getElementById("lead-email").value.trim();
    const company  = document.getElementById("lead-company").value.trim();
    const role     = document.getElementById("lead-role").value.trim();
    const industry = document.getElementById("lead-industry").value;
    const phone    = document.getElementById("lead-phone").value.trim();

    if (!name || !email || !company || !industry) {
        alert("Please fill in Name, Email, Company and Industry.");
        return;
    }
    const btn = document.getElementById("lead-submit-btn");
    btn.disabled = true; btn.innerText = "Submitting...";
    try {
        const res  = await fetch(API_LEAD, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                name, email, company, role, industry, phone,
                session_id: sessionId, buying_signals: detectedSignals,
                utm_source: utmSource, utm_medium: utmMedium, utm_campaign: utmCampaign,
            })
        });
        const data = await res.json();
        if (data.success) {
            closeLeadForm();
            const chatBox = document.getElementById("chat");
            const c = document.createElement("div");
            c.className = "message bot";
            c.innerText = "✅ " + data.message;
            chatBox.appendChild(c);
            chatBox.scrollTop = chatBox.scrollHeight;
        } else {
            alert("Something went wrong. Please try again.");
        }
    } catch(e) {
        alert("Could not submit. Please check your connection.");
    } finally {
        btn.disabled = false; btn.innerText = "Submit";
    }
}

// ─── Render + helpers ──────────────────────────────────────────────────────────

function renderChat() {
    const chatBox = document.getElementById("chat");
    chatBox.innerHTML = "";
    if (!currentChat || !chats[currentChat]) return;
    chats[currentChat].forEach(msg => {
        const div     = document.createElement("div");
        div.className = `message ${msg.role}`;
        div.innerText = msg.text;
        chatBox.appendChild(div);
    });
    chatBox.scrollTop = chatBox.scrollHeight;
}

function renderHistory() {
    const history = document.getElementById("history");
    history.innerHTML = "";
    Object.keys(chats).reverse().forEach(id => {
        const div     = document.createElement("div");
        div.className = "history-item" + (id === currentChat ? " active" : "");
        div.innerText = chats[id][0]?.text?.slice(0, 40) || "New Chat";
        div.onclick   = () => { currentChat = id; renderChat(); };
        history.appendChild(div);
    });
}

function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("active");
}

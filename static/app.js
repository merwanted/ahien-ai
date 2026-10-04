/* DataMedX Frontend - Chat & UI Logic */
(function () {
    "use strict";

    // --- DOM Elements ---
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const chatContainer = document.getElementById("chat-container");
    const cancerFilter = document.getElementById("cancer-filter");
    const statusDot = document.querySelector(".status-dot");
    const statusText = document.getElementById("status-text");
    const exampleBtns = document.querySelectorAll(".example-btn");

    let isGenerating = false;

    // --- Init ---
    checkHealth();
    loadStats();
    setupListeners();
    setupNavbar();
    setupCounters();

    // --- Health Check ---
    async function checkHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            statusDot.classList.add("online");
            const mode = data.mode === "cloud" ? "Cloud" : "Yerel";
            statusText.textContent = `${mode} · ${data.model} · ${data.chunk_count} chunk`;
            if (!data.indexed) {
                statusText.textContent = "⚠️ İndekslenmemiş - python indexer.py çalıştırın";
                statusDot.classList.remove("online");
            }
        } catch {
            statusText.textContent = "Bağlantı hatası";
            statusDot.classList.remove("online");
        }
    }

    // --- Load Stats for Disease Cards ---
    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            if (data.kanser) {
                const map = {
                    "Karaciğer kanseri": "dc-karaciger",
                    "Meme Kanseri": "dc-meme",
                    "Multipl miyelom": "dc-miyelom",
                    "Over kanseri": "dc-over",
                    "Prostat kanseri": "dc-prostat",
                };
                for (const [k, id] of Object.entries(map)) {
                    const el = document.getElementById(id);
                    if (el) el.textContent = data.kanser[k] || 0;
                }
            }
        } catch { /* silent */ }
    }

    // --- Listeners ---
    function setupListeners() {
        sendBtn.addEventListener("click", sendMessage);
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
        chatInput.addEventListener("input", autoResize);
        exampleBtns.forEach((btn) => {
            btn.addEventListener("click", () => {
                chatInput.value = btn.dataset.q;
                sendMessage();
            });
        });
        // Disease card click -> filter + scroll to chat
        document.querySelectorAll(".disease-card").forEach((card) => {
            card.addEventListener("click", () => {
                const cancer = card.dataset.cancer;
                if (cancer && cancerFilter) {
                    cancerFilter.value = cancer;
                    document.getElementById("chatbot").scrollIntoView({ behavior: "smooth" });
                }
            });
        });
    }

    function autoResize() {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
    }

    // --- Send Message ---
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || isGenerating) return;

        isGenerating = true;
        sendBtn.disabled = true;
        chatInput.value = "";
        chatInput.style.height = "auto";

        // Hide examples
        const exQ = document.getElementById("example-questions");
        if (exQ) exQ.style.display = "none";

        // User bubble
        appendMessage("user", text);

        // Bot typing
        const botDiv = appendMessage("bot", null, true);
        const contentEl = botDiv.querySelector(".message-content");

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, filter: cancerFilter.value }),
            });

            if (!res.ok) {
                const err = await res.json();
                contentEl.innerHTML = `<p style="color:var(--accent-rose)">Hata: ${err.error || "Bilinmeyen hata"}</p>`;
                finishGen();
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullText = "";
            let sources = [];
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.sources) { sources = data.sources; continue; }
                        if (data.error) {
                            fullText += `\n\n**Hata:** ${data.error}`;
                            renderMarkdown(contentEl, fullText);
                            continue;
                        }
                        if (data.token) {
                            fullText += data.token;
                            renderMarkdown(contentEl, fullText);
                            scrollBottom();
                        }
                        if (data.done) {
                            if (sources.length > 0) addSources(contentEl, sources);
                        }
                    } catch { /* skip bad json */ }
                }
            }
        } catch (err) {
            contentEl.innerHTML = `<p style="color:var(--accent-rose)">Bağlantı hatası: ${err.message}</p>`;
        }

        // Remove typing indicator
        const typing = contentEl.querySelector(".typing-indicator");
        if (typing) typing.remove();

        finishGen();
    }

    function finishGen() {
        isGenerating = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }

    // --- Append Message ---
    function appendMessage(role, text, isTyping = false) {
        const div = document.createElement("div");
        div.className = `message ${role === "user" ? "user-message" : "bot-message"}`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = role === "user" ? "👤" : "🤖";

        const content = document.createElement("div");
        content.className = "message-content";

        if (isTyping) {
            content.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
        } else if (text) {
            renderMarkdown(content, text);
        }

        div.appendChild(avatar);
        div.appendChild(content);
        chatMessages.appendChild(div);
        scrollBottom();
        return div;
    }

    function addSources(contentEl, sources) {
        const div = document.createElement("div");
        div.className = "message-sources";
        const unique = [...new Map(sources.map((s) => [`${s.kanser}-${s.tip}`, s])).values()];
        unique.forEach((s) => {
            const badge = document.createElement("span");
            badge.className = "source-badge";
            badge.textContent = `${s.kanser} · ${s.tip}`;
            div.appendChild(badge);
        });
        contentEl.appendChild(div);
    }

    function scrollBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // --- Simple Markdown Renderer ---
    function renderMarkdown(el, text) {
        let html = text
            // Escape HTML
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            // Headers
            .replace(/^#### (.+)$/gm, "<h4>$1</h4>")
            .replace(/^### (.+)$/gm, "<h3>$1</h3>")
            .replace(/^## (.+)$/gm, "<h3>$1</h3>")
            // Bold & italic
            .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.+?)\*/g, "<em>$1</em>")
            // Code
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            // Unordered lists
            .replace(/^\s*[-*]\s+(.+)$/gm, "<li>$1</li>")
            // Ordered lists
            .replace(/^\s*\d+\.\s+(.+)$/gm, "<li>$1</li>")
            // Horizontal rule
            .replace(/^---$/gm, "<hr>")
            // Line breaks -> paragraphs
            .replace(/\n\n+/g, "</p><p>")
            .replace(/\n/g, "<br>");

        // Wrap lists
        html = html.replace(/((?:<li>.*<\/li>\s*)+)/g, "<ul>$1</ul>");
        // Wrap in p
        html = `<p>${html}</p>`;
        // Clean empty p
        html = html.replace(/<p>\s*<\/p>/g, "").replace(/<p>\s*(<h[34]>)/g, "$1").replace(/(<\/h[34]>)\s*<\/p>/g, "$1");

        // Keep typing indicator if present
        const typing = el.querySelector(".typing-indicator");
        el.innerHTML = html;
        if (typing) el.appendChild(typing);
    }

    // --- Navbar Scroll ---
    function setupNavbar() {
        const nav = document.getElementById("navbar");
        window.addEventListener("scroll", () => {
            nav.classList.toggle("scrolled", window.scrollY > 50);
        });
        // Mobile menu
        const btn = document.getElementById("mobile-menu-btn");
        const links = document.querySelector(".nav-links");
        if (btn && links) {
            btn.addEventListener("click", () => {
                links.style.display = links.style.display === "flex" ? "none" : "flex";
                links.style.flexDirection = "column";
                links.style.position = "absolute";
                links.style.top = "100%";
                links.style.left = "0";
                links.style.right = "0";
                links.style.background = "rgba(11,15,26,0.98)";
                links.style.padding = "1rem 1.5rem";
                links.style.borderBottom = "1px solid var(--border-glass)";
            });
        }
    }

    // --- Animated Counters ---
    function setupCounters() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateCounters();
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.3 }
        );
        const section = document.getElementById("stats-section");
        if (section) observer.observe(section);
    }

    function animateCounters() {
        document.querySelectorAll(".stat-card").forEach((card) => {
            const target = parseInt(card.dataset.target, 10);
            const numEl = card.querySelector(".stat-number");
            if (!numEl || !target) return;
            let current = 0;
            const step = Math.max(1, Math.floor(target / 40));
            const interval = setInterval(() => {
                current += step;
                if (current >= target) { current = target; clearInterval(interval); }
                numEl.textContent = current.toLocaleString("tr-TR");
            }, 30);
        });
    }
})();

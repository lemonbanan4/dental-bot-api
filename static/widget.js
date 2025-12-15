(() => {
  // Simple Dental Bot embed widget.
  // Usage in your site: <script src="http://localhost:8000/static/widget.js"></script>
  // Then call: window.DentalBotWidget.init({ apiUrl: "http://localhost:8000", clinicId: "smile-city-001" })

  const defaultOptions = {
    apiUrl: "http://localhost:8000",
    clinicId: "",
    buttonLabel: "Chat with us",
    title: "Dental Assistant",
  };

  const styles = `
    .dbot-launcher {
      position: fixed; right: 20px; bottom: 20px;
      background: #2563eb; color: #fff; border: none;
      border-radius: 999px; padding: 12px 16px;
      font: 600 14px/1.2 system-ui, -apple-system, sans-serif;
      cursor: pointer; box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    .dbot-panel {
      position: fixed; right: 20px; bottom: 70px; width: 320px; height: 420px;
      background: #fff; border-radius: 12px; box-shadow: 0 10px 35px rgba(0,0,0,0.18);
      display: none; flex-direction: column; overflow: hidden; border: 1px solid #e5e7eb;
      font: 14px/1.4 system-ui, -apple-system, sans-serif;
    }
    .dbot-panel.open { display: flex; }
    .dbot-header { padding: 12px 14px; background: #1d4ed8; color: #fff; font-weight: 700; }
    .dbot-messages { flex: 1; padding: 12px; overflow-y: auto; gap: 8px; display: flex; flex-direction: column; }
    .dbot-msg { padding: 10px 12px; border-radius: 10px; max-width: 90%; }
    .dbot-msg.user { background: #e0f2fe; align-self: flex-end; }
    .dbot-msg.bot { background: #f3f4f6; align-self: flex-start; }
    .dbot-input { display: flex; padding: 10px; gap: 8px; border-top: 1px solid #e5e7eb; }
    .dbot-input textarea { flex: 1; resize: none; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px; min-height: 50px; font: inherit; }
    .dbot-input button { background: #2563eb; color: #fff; border: none; padding: 10px 12px; border-radius: 8px; cursor: pointer; font-weight: 600; }
  `;

  function ensureStyleTag() {
    if (document.getElementById("dbot-styles")) return;
    const tag = document.createElement("style");
    tag.id = "dbot-styles";
    tag.textContent = styles;
    document.head.appendChild(tag);
  }

  function createElements(opts) {
    const launcher = document.createElement("button");
    launcher.className = "dbot-launcher";
    launcher.textContent = opts.buttonLabel;

    const panel = document.createElement("div");
    panel.className = "dbot-panel";

    const header = document.createElement("div");
    header.className = "dbot-header";
    header.textContent = opts.title;

    const messages = document.createElement("div");
    messages.className = "dbot-messages";

    const inputWrap = document.createElement("div");
    inputWrap.className = "dbot-input";

    const textarea = document.createElement("textarea");
    textarea.placeholder = "Type your question...";

    const sendBtn = document.createElement("button");
    sendBtn.textContent = "Send";

    inputWrap.appendChild(textarea);
    inputWrap.appendChild(sendBtn);

    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(inputWrap);

    document.body.appendChild(launcher);
    document.body.appendChild(panel);

    return { launcher, panel, messages, textarea, sendBtn };
  }

  function addMessage(container, text, who) {
    const div = document.createElement("div");
    div.className = `dbot-msg ${who}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  async function sendMessage(opts, ui, state) {
    const text = ui.textarea.value.trim();
    if (!text || state.sending) return;
    state.sending = true;
    ui.sendBtn.disabled = true;
    addMessage(ui.messages, text, "user");
    ui.textarea.value = "";

    try {
      const res = await fetch(`${opts.apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clinic_id: opts.clinicId,
          message: text,
          session_id: state.sessionId || opts.sessionId || `sess-${Date.now()}`,
        }),
      });
      if (!res.ok) {
        let detail = "";
        try {
          const errData = await res.json();
          detail = errData?.detail ? `: ${errData.detail}` : "";
        } catch (_) {
          /* ignore json parsing */
        }
        addMessage(ui.messages, `Error ${res.status}${detail}`, "bot");
        return;
      }
      const data = await res.json();
      if (data.session_id) {
        state.sessionId = data.session_id;
      }
      addMessage(ui.messages, data.reply || "(no reply)", "bot");
    } catch (err) {
      const msg = err?.message || err;
      addMessage(ui.messages, `Network error: ${msg}`, "bot");
    } finally {
      state.sending = false;
      ui.sendBtn.disabled = false;
      ui.textarea.focus();
    }
  }

  function whenReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  function init(userOpts = {}) {
    const opts = { ...defaultOptions, ...userOpts };
    if (!opts.clinicId) {
      console.warn("DentalBotWidget: clinicId is required");
      return;
    }
    const state = { sessionId: opts.sessionId || null, sending: false };
    const setup = () => {
      ensureStyleTag();
      const ui = createElements(opts);
      ui.launcher.onclick = () => {
        ui.panel.classList.toggle("open");
      };
      const triggerSend = () => sendMessage(opts, ui, state);
      ui.sendBtn.onclick = triggerSend;
      ui.textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          triggerSend();
        }
      });
    };
    whenReady(setup);
  }

  window.DentalBotWidget = { init };
})();

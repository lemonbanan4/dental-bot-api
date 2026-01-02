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
    :root{ --dbot-accent: #2563eb; }
    .dbot-launcher {
      position: fixed; right: 20px; bottom: 20px;
      background: var(--dbot-accent); color: #fff; border: none;
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
    .dbot-input button { background: var(--dbot-accent); color: #fff; border: none; padding: 10px 12px; border-radius: 8px; cursor: pointer; font-weight: 600; }
    .dbot-msg-actions{display:flex;gap:8px;margin-top:8px}
    .dbot-msg-action{background:#fff;border:1px solid #e6e6e6;padding:6px 8px;border-radius:8px;font-weight:700;cursor:pointer}
    .dbot-msg-action.primary{background:var(--dbot-accent);color:#fff;border-color:transparent}
    .dbot-modal-backdrop{position:fixed;right:20px;bottom:80px;width:360px;display:none;z-index:1000000;align-items:flex-end;justify-content:flex-end}
    .dbot-modal{width:100%;background:#fff;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden;border:1px solid #e5e7eb;transform:translateY(12px);transition:transform .18s ease,opacity .18s ease}
    .dbot-modal.open{transform:translateY(0)}
    .dbot-modal-h{padding:12px 12px;background:var(--dbot-accent);color:#fff;font-weight:800;display:flex;justify-content:space-between;align-items:center}
    .dbot-modal-c{padding:12px;display:flex;flex-direction:column;gap:10px}
  `;

  function ensureStyleTag() {
    if (document.getElementById("dbot-styles")) return;
    const tag = document.createElement("style");
    tag.id = "dbot-styles";
    tag.textContent = styles;
    document.head.appendChild(tag);
  }

  function linkifyToFragment(text) {
    const urlRegex = /(https?:\/\/[^\s)]+)\b/g;
    const parts = String(text).split(urlRegex);
    const frag = document.createDocumentFragment();
    for (const part of parts) {
      if (urlRegex.test(part)) {
        const a = document.createElement('a');
        a.href = part;
        a.textContent = part;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        frag.appendChild(a);
      } else {
        frag.appendChild(document.createTextNode(part));
      }
    }
    return frag;
  }

  function createElements(opts) {
    const launcher = document.createElement("button");
    launcher.className = "dbot-launcher";
    launcher.textContent = opts.buttonLabel;

    const panel = document.createElement("div");
    panel.className = "dbot-panel";

    launcher.dataset.bookingUrl = "";
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


    // Lead modal (non-blocking slide-in)
    const backdrop = document.createElement('div');
    backdrop.className = 'dbot-modal-backdrop';
    backdrop.innerHTML = `
      <div class="dbot-modal" role="dialog" aria-modal="true">
        <div class="dbot-modal-h">
          <div>Request a callback</div>
          <button class="dbot-close" aria-label="Close">×</button>
        </div>
        <div class="dbot-modal-c">
          <div>
            <label>Name (optional)</label>
            <input type="text" class="dbot-name" placeholder="Your name" />
          </div>
          <div>
            <label>Phone (recommended)</label>
            <input type="text" class="dbot-phone" placeholder="+46 ..." />
          </div>
          <div>
            <label>Message (optional)</label>
            <textarea class="dbot-lead-msg" rows="3" placeholder="What is this about?"></textarea>
          </div>
          <div style="display:flex;gap:8px;justify-content:flex-end">
            <button class="dbot-btn cancel">Cancel</button>
            <button class="dbot-btn primary submit">Send</button>
          </div>
          <div class="dbot-lead-status" style="font-size:12px;color:#444;"></div>
        </div>
      </div>
    `;

    return { launcher, panel, messages, textarea, sendBtn };
  }
    document.body.appendChild(backdrop);

  function addMessage(container, text, who) {
    const div = document.createElement("div");
    div.className = `dbot-msg ${who}`;
      // Render message text with clickable links (innerHTML replacement)
      try {
        // safe DOM-based linkification
        const frag = linkifyToFragment(String(text));
        div.appendChild(frag);
      } catch (e) {
        div.appendChild(document.createTextNode(String(text)));
      }
    container.appendChild(div);
    // render primary CTAs after assistant messages
    if (who === 'bot') {
      const acts = document.createElement('div');
      acts.className = 'dbot-msg-actions';
      const b = document.createElement('button');
      b.className = 'dbot-msg-action primary';
      b.type = 'button';
      b.textContent = '📅 Book appointment';
      const bookingUrl = (window.DentalBotWidget && window.DentalBotWidget._launcher && window.DentalBotWidget._launcher.dataset.bookingUrl) || '';
      if (!bookingUrl) b.disabled = true;
      b.onclick = () => {
        const url = bookingUrl || (window.DentalBotWidget && window.DentalBotWidget._launcher && window.DentalBotWidget._launcher.dataset.bookingUrl) || '';
        if (url) window.open(url, '_blank', 'noopener,noreferrer');
      };
      acts.appendChild(b);
      const cb = document.createElement('button');
      cb.className = 'dbot-msg-action';
      cb.type = 'button';
      cb.textContent = '📞 Request callback';
      cb.onclick = () => {
        // open modal
        openLeadModal(window.DentalBotWidget._ui);
      };
      acts.appendChild(cb);
      container.appendChild(acts);
    }
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
      // store booking url on launcher for per-message CTAs
      if (data.booking_url && ui && ui.launcher) {
        ui.launcher.dataset.bookingUrl = data.booking_url;
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
      // expose ui/launcher for static hook usage
      window.DentalBotWidget._launcher = ui.launcher;
      window.DentalBotWidget._ui = ui;
      // apply theme if provided
      if (opts.theme) {
        try { document.documentElement.style.setProperty('--dbot-accent', opts.theme); } catch (e) {}
      }
      ui.launcher.onclick = () => {
        ui.panel.classList.toggle("open");
      };
      // modal controls
      const backdrop = document.querySelector('.dbot-modal-backdrop');
      if (backdrop) {
        backdrop.addEventListener('click', (e) => { if (e.target === backdrop) closeLeadModal(ui); });
        const cancel = backdrop.querySelector('.cancel');
        if (cancel) cancel.onclick = () => closeLeadModal(ui);
        const close = backdrop.querySelector('.dbot-close');
        if (close) close.onclick = () => closeLeadModal(ui);
        const submit = backdrop.querySelector('.submit');
        if (submit) submit.onclick = () => submitLead(ui, state);
      }
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

  function openLeadModal(ui) {
    if (!ui || !ui.launcher) return;
    const backdrop = document.querySelector('.dbot-modal-backdrop');
    if (!backdrop) return;
    backdrop.style.display = 'flex';
    const modal = backdrop.querySelector('.dbot-modal');
    if (modal) modal.classList.add('open');
    const nameEl = backdrop.querySelector('.dbot-name');
    try { if (nameEl) nameEl.focus({ preventScroll: true }); } catch (e) { if (nameEl) nameEl.focus(); }
  }

  function closeLeadModal(ui) {
    const backdrop = document.querySelector('.dbot-modal-backdrop');
    if (!backdrop) return;
    const modal = backdrop.querySelector('.dbot-modal');
    if (modal) modal.classList.remove('open');
    backdrop.style.display = 'none';
    const status = backdrop.querySelector('.dbot-lead-status'); if (status) status.textContent = '';
  }

  async function submitLead(ui, state) {
    const backdrop = document.querySelector('.dbot-modal-backdrop');
    if (!backdrop) return;
    const name = backdrop.querySelector('.dbot-name').value.trim() || null;
    const phone = backdrop.querySelector('.dbot-phone').value.trim() || null;
    const message = backdrop.querySelector('.dbot-lead-msg').value.trim() || null;
    const status = backdrop.querySelector('.dbot-lead-status');
    if (status) status.textContent = 'Sending…';
    try {
      const res = await fetch(`${opts.apiUrl}/leads`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clinic_id: opts.clinicId, session_id: state.sessionId, name, phone, message })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (status) status.textContent = `Error ${res.status}: ${data.detail || 'Could not send'}`;
        return;
      }
      if (status) status.textContent = "Sent! The clinic will contact you.";
      try { addMessage(window.DentalBotWidget._ui.messages, "We'll call you shortly — thank you!", 'bot'); } catch (e) {}
      setTimeout(() => closeLeadModal(ui), 900);
    } catch (e) {
      if (status) status.textContent = 'Network error. Please try again.';
    }
  }

  window.DentalBotWidget = { init };
})();

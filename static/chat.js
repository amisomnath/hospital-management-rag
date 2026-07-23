const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const statusBadge = document.querySelector("#connection-status");
const activity = document.querySelector("#activity");

const loginForm = document.querySelector("#login-form");
const authStatus = document.querySelector("#auth-status");
const sessionId = crypto.randomUUID();
let socket = null;

function appendMessage(role, text, sources = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const heading = document.createElement("strong");
  heading.textContent = role === "user" ? "You" : "Assistant";
  article.appendChild(heading);

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);

  if (sources.length) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `Sources (${sources.length})`;
    details.appendChild(summary);

    for (const source of sources) {
      const item = document.createElement("div");
      item.className = "source";
      item.textContent = `${source.document} · score ${Number(source.score).toFixed(3)} — ${source.content}`;
      details.appendChild(item);
    }
    article.appendChild(details);
  }

  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function connect(token) {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const encodedToken = encodeURIComponent(token);
  socket = new WebSocket(
    `${protocol}://${window.location.host}/api/v1/chat/ws/${sessionId}?token=${encodedToken}`
  );

  socket.addEventListener("open", () => {
    statusBadge.textContent = "Connected";
    statusBadge.className = "status status-online";
    loginForm.hidden = true;
    authStatus.textContent = "";
  });

  socket.addEventListener("close", () => {
    statusBadge.textContent = "Disconnected";
    statusBadge.className = "status status-offline";
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "status") {
      activity.textContent = data.message;
      return;
    }
    if (data.type === "answer" || data.type === "rejected") {
      activity.textContent = "";
      appendMessage("assistant", data.answer, data.sources || []);
      return;
    }
    if (data.type === "error") {
      activity.textContent = "";
      appendMessage("assistant", data.message || "An error occurred.");
    }
  });
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  authStatus.textContent = "Signing in...";
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: document.querySelector("#email").value,
      password: document.querySelector("#password").value,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    authStatus.textContent = data.detail || "Sign-in failed.";
    return;
  }
  connect(data.access_token);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || socket.readyState !== WebSocket.OPEN) return;

  appendMessage("user", message);
  socket.send(JSON.stringify({ type: "chat_message", message }));
  input.value = "";
  input.focus();
});

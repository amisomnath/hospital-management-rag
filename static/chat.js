const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const statusBadge = document.querySelector("#connection-status");
const activity = document.querySelector("#activity");

const sessionId = crypto.randomUUID();
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(`${protocol}://${window.location.host}/api/v1/chat/ws/${sessionId}`);

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

socket.addEventListener("open", () => {
  statusBadge.textContent = "Connected";
  statusBadge.className = "status status-online";
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

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || socket.readyState !== WebSocket.OPEN) return;

  appendMessage("user", message);
  socket.send(JSON.stringify({ type: "chat_message", message }));
  input.value = "";
  input.focus();
});

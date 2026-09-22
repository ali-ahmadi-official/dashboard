const messagesDiv = document.getElementById("messages");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const card = document.querySelector(".card");
const msg = document.querySelectorAll(".msg");
const toggleButton = document.getElementById('toggle-button');
const listPanel = document.getElementById('list-panel');
const now = new Date();

const path = window.location.pathname;
const match = path.match(/\/chat-bot\/(\d+)(?:\/|$)/);

let pk = ""
if (match) {
    pk = match[1];
}

messagesDiv.scrollTop = messagesDiv.scrollHeight;

const observer = new MutationObserver(() => {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
});

observer.observe(messagesDiv, { childList: true });

const down = document.getElementById('down');
const threshold = 80;

function checkScrollability() {
    if (messagesDiv.scrollHeight <= messagesDiv.clientHeight) {
        down.classList.add('hidden');
    } else {
        if (messagesDiv.scrollTop + messagesDiv.clientHeight >= messagesDiv.scrollHeight - threshold) {
            down.classList.add('hidden');
        } else {
            down.classList.remove('hidden');
        }
    }
}

messagesDiv.addEventListener('scroll', checkScrollability);

down.addEventListener('click', () => {
    messagesDiv.scrollTo({
        top: messagesDiv.scrollHeight,
        behavior: 'smooth'
    });
});

window.addEventListener('load', checkScrollability);

window.togglePanel = function () {
    listPanel.classList.toggle('list-panel-hidden');
};

toggleButton.addEventListener('click', togglePanel);

const closeButton = document.querySelector('.close-button');
if (closeButton) {
    closeButton.addEventListener('click', (event) => {
        event.stopPropagation();
        togglePanel();
    });
}

const listItems = listPanel.querySelectorAll('li');
listItems.forEach(item => {
    item.addEventListener('click', () => {
        togglePanel();
    });
});

if (msg.length !== 0) {
    card.style.display = "none";
}

let data = null;

function formatAIMessage(text) {
    if (!text) return "";

    const html = marked.parse(text, {
        breaks: true,
        gfm: true
    });

    return DOMPurify.sanitize(html);
}

function renderMessage(role, text) {
    const currentTime = new Date();
    const timeStr = `${String(currentTime.getHours()).padStart(2, "0")}:${String(currentTime.getMinutes()).padStart(2, "0")}`;

    if (role === "ai") {
        const wrapper = document.createElement("div");
        wrapper.className = "ai-wrapper";

        const avatar = document.createElement("div");
        avatar.className = "ai-avatar";

        const img = document.createElement("img");
        img.src = "/static/img/ai.png";        
        img.alt = "ai";
        img.className = "ai-img";

        const bubble = document.createElement("div");
        bubble.className = "msg ai";
        bubble.dir = "rtl";

        const textSpan = document.createElement("span");
        textSpan.className = "msg-text";
        textSpan.innerHTML = text;

        const timeSpan = document.createElement("span");
        timeSpan.className = "msg-time";
        timeSpan.style.fontSize = "smaller";
        timeSpan.textContent = timeStr;

        bubble.appendChild(textSpan);
        bubble.appendChild(document.createElement("br"));
        bubble.appendChild(document.createElement("br"));
        bubble.appendChild(timeSpan);

        avatar.appendChild(img);
        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);

        messagesDiv.appendChild(wrapper);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return bubble;
    }

    const div = document.createElement("div");
    div.className = "msg user";
    div.dir = "rtl";

    const textSpan = document.createElement("span");
    textSpan.className = "msg-text";
    textSpan.innerHTML = text;

    const timeSpan = document.createElement("span");
    timeSpan.className = "msg-time";
    timeSpan.style.fontSize = "smaller";
    timeSpan.textContent = timeStr;

    div.appendChild(textSpan);
    div.appendChild(document.createElement("br"));
    div.appendChild(document.createElement("br"));
    div.appendChild(timeSpan);

    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

sendBtn.onclick = async () => {
    if (!card.classList.contains("hidden")) {
        card.classList.add("hidden");
    }
    const userText = input.value.trim();
    if (!userText) return;

    renderMessage("user", userText);

    input.value = "";
    sendBtn.disabled = true;
    input.disabled = true;

    const aiDiv = renderMessage("ai", `
        <span class="typing-indicator">
            <span></span><span></span><span></span>
        </span>
    `);

    try {
        const response = await fetch("/chat-api/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                pk: pk,
                userText: userText
            })
        });

        const data = await response.json();
        const textSpan = aiDiv.querySelector(".msg-text");

        if (data.reply) {
            textSpan.innerHTML = formatAIMessage(data.reply);
        } else {
            textSpan.innerHTML = "خطا در دریافت پاسخ";
        }

        if (data.chat_id && data.chat_id !== pk) {
            
            pk = data.chat_id;

            if (window.location.pathname === '/chat-bot/') {
                window.location.href = `/chat-bot/${pk}/`;
            }
        }

    } catch (err) {
        aiDiv.querySelector(".msg-text").innerText = "خطا در ارتباط با سرور";
    }

    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
};

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !sendBtn.disabled) {
        event.preventDefault();
        sendBtn.click();
    }
});
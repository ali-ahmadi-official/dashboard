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

function renderMessage(role, text) {
    if (role === "ai") {
        const wrapper = document.createElement("div");
        wrapper.className = "ai-wrapper";

        const avatar = document.createElement("div");
        avatar.className = "ai-avatar";

        const img = document.createElement("img");
        img.src = "/static/img/ai.jpg";        
        img.alt = "ai";
        img.className = "ai-img";

        const bubble = document.createElement("div");
        bubble.className = "msg ai";
        bubble.dir = "rtl";
        bubble.innerHTML = text; 
        bubble.innerHTML += `<br><br><span style="font-size: smaller;">${now.getHours()}:${now.getMinutes()}</span>`;

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
    div.innerHTML = text; 
    div.innerHTML += `<br><br><span style="font-size: smaller;">${now.getHours()}:${now.getMinutes()}</span>`;

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

    const aiDiv = renderMessage("ai", "...");

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

        if (data.reply) {
            aiDiv.innerText = data.reply
            aiDiv.innerHTML += `<br><br><span style="font-size: smaller;">${now.getHours()}:${now.getMinutes()}</span>`;
        } else {
            aiDiv.innerText = "خطا در دریافت پاسخ"
            aiDiv.innerHTML += `<br><br><span style="font-size: smaller;">${now.getHours()}:${now.getMinutes()}</span>`;
        }

        if (data.chat_id && data.chat_id !== pk) {
            
            pk = data.chat_id;

            if (window.location.pathname === '/chat-bot/') {
                window.location.href = `/chat-bot/${pk}/`;
            }
        }

    } catch (err) {
        aiDiv.innerText = "خطا در ارتباط با سرور";
        aiDiv.innerHTML += `<br><br><span style="font-size: smaller;">${now.getHours()}:${now.getMinutes()}</span>`;
    }

    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
};

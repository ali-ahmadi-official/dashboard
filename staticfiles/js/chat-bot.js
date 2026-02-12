const messagesDiv = document.getElementById("messages");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const card = document.querySelector(".card");
const msg = document.querySelectorAll(".msg");

if (msg.length !== 0) {
    card.style.display = "none";
}

let data = null;
let chatHistory = [];

function renderMessage(role, text) {
    if (role === "ai") {
        const wrapper = document.createElement("div");
        wrapper.className = "ai-wrapper";

        const avatar = document.createElement("div");
        avatar.className = "ai-avatar";

        const img = document.createElement("img");
        img.src = "../static/img/ai.jpg";
        img.alt = "ai";
        img.className = "ai-img";

        const bubble = document.createElement("div");
        bubble.className = "msg ai";
        bubble.dir = "rtl";
        bubble.innerText = text;

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
    div.innerText = text;

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

    // نمایش پیام کاربر
    renderMessage("user", userText);
    chatHistory.push(`پیام کاربر:\n${userText}`);

    input.value = "";
    sendBtn.disabled = true;
    input.disabled = true;

    // پیام موقت AI
    const aiDiv = renderMessage("ai", "...");

    try {
        const response = await fetch("/chat-api/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                chat_history: chatHistory
            })
        });

        const data = await response.json();

        if (data.reply) {
            aiDiv.innerText = data.reply;
            chatHistory.push(`پاسخ هوش مصنوعی:\n${data.reply}`);
        } else {
            aiDiv.innerText = "خطا در دریافت پاسخ";
        }

    } catch (err) {
        aiDiv.innerText = "خطا در ارتباط با سرور";
    }

    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
};

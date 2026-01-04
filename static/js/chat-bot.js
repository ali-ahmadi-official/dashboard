const API_URL = "https://api.gapgpt.app/v1/chat/completions";
const API_KEY = "sk-AdPmxjn95ilaIvMy3sESV8jH5lQJxtftHURitD5Xfn1RKmSg";

const messagesDiv = document.getElementById("messages");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

let data = null;

sendBtn.disabled = true;

fetch("../static/json/conditions.json")
    .then(res => res.json())
    .then(json => {
        data = json;
        sendBtn.disabled = false;
    });

const rule_1 = `
تو یک دستیار هوش مصنوعی فارسی هستی. فقط پاسخ واضح و روان بده.
`;

const rule_2 = `
تمامی پیام های من به تو، درواقع شامل ساعت کنونی مکالمه و تاریخچه چت مربوطه فردی با توست که:
متن زیر عبارت 'پیام کاربر' را فرد گفتگو کننده داده
و متن زیر عبارت 'پاسخ هوش مصنوعی' را تو داده بودی
بنابراین تو فقط باید باتوجه به ساعت کنونی مکالمه و تاریخچه، پاسخ آخرین پیام کاربر را بدهی.
ساعت کنونی رو از کاربر نپرس و فقط از ساعت کنونی مکالمه که من میدم استفاده کن.
`;

const rule_3 = () => JSON.stringify(data, null, 2);

let chatHistory = [];

function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString("fa-IR", { hour: "2-digit", minute: "2-digit" });
}

function renderMessage(role, text) {
    if (role === "ai") {
        const wrapper = document.createElement("div");
        wrapper.className = "ai-wrapper";

        const avatar = document.createElement("div");
        avatar.className = "ai-avatar";

        const img = document.createElement("img");
        img.src = "../static/img/ai.avif";
        img.alt = "ai";
        img.className = "ai-img";

        const bubble = document.createElement("div");
        bubble.className = "msg ai";
        bubble.dir = "rtl";
        bubble.innerText = text;

        avatar.appendChild(img)
        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);

        messagesDiv.appendChild(wrapper);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return bubble;
    }

    const div = document.createElement("div");
    div.className = `msg user`;
    div.dir = "rtl";
    div.innerText = text;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

sendBtn.onclick = async () => {
    const userText = input.value.trim();
    if (!userText) return;

    // افزودن پیام کاربر
    renderMessage("user", userText);
    chatHistory.push(`پیام کاربر:\n${userText}`);

    input.value = "";
    sendBtn.disabled = true;
    input.disabled = true;

    // پیام موقت AI
    const aiDiv = renderMessage("ai", "...");

    // ساخت متن ارسالی به AI
    const payloadText = `
        ساعت کنونی مکالمه:
        ${getCurrentTime()}

        تاریخچه مکالمه:
        ${chatHistory.join("\n")}
    `;

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${API_KEY}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: "gpt-4o-mini",
                messages: [
                    { role: "system", content: rule_1 },
                    { role: "system", content: rule_2 },
                    { role: "system", content: rule_3() },
                    { role: "user", content: payloadText }
                ]
            })
        });

        const data = await response.json();

        if (data.choices) {
            const aiText = data.choices[0].message.content;
            aiDiv.innerText = aiText;
            chatHistory.push(`پاسخ هوش مصنوعی:\n${aiText}`);
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

const elements = document.querySelectorAll('.msg-text');

function formatAIMessage(text) {
    if (!text) return "";

    const html = marked.parse(text, {
        breaks: true,
        gfm: true
    });

    return DOMPurify.sanitize(html);
}

elements.forEach(element => {
    element.innerHTML = formatAIMessage(element.textContent);
});
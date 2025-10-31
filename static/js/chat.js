const scrollingBox = document.getElementById('chat-content');
scrollingBox.scrollTop = scrollingBox.scrollHeight;

const observer = new MutationObserver(() => {
    scrollingBox.scrollTop = scrollingBox.scrollHeight;
});

observer.observe(scrollingBox, { childList: true });

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// function fetchMessages() {
//     const lastMessageId = $('#chat-content .media-chat').last().attr('id') || 0;
//     const chatId = window.location.pathname.split('/')[2];
//     const requestUrl = `/chats/${chatId}/update/?after_id=${lastMessageId}`;

//     $.ajax({
//         url: requestUrl,
//         type: 'GET',
//         success: function (data) {
//             if (data.trim().length > 0) {
//                 const atBottom = scrollingBox.scrollTop + scrollingBox.clientHeight >= scrollingBox.scrollHeight - 50;
//                 $('#chat-content').append(data);

//                 if (atBottom) {
//                     scrollingBox.scrollTop = scrollingBox.scrollHeight;
//                 }
//             }
//         }
//     });
// }

$(document).ready(function () {
    setInterval(fetchMessages, 5000);
});

$(document).ready(function () {
    $("#load-older").on("click", function () {
        var chatContent = $("#chat-content");
        var firstMessageId = $(".media-chat").first().attr("id");

        var oldScrollHeight = chatContent[0].scrollHeight;
        var oldScrollTop = chatContent.scrollTop();

        $.ajax({
            url: window.location.pathname.replace(/\/$/, "") + "/load_older/",
            data: { "before_id": firstMessageId },
            success: function (data) {
                $("#load-older").after(data);

                requestAnimationFrame(function () {
                    var newScrollHeight = chatContent[0].scrollHeight;
                    var diff = newScrollHeight - oldScrollHeight;
                    chatContent.scrollTop(oldScrollTop + diff);
                });

                if ($("#no-more-messages").length > 0) {
                    $("#load-older").text("📜 پیام قدیمی تری موجود نیست").css("color", "gray");
                    $("#load-older").off("click");
                }
            }
        });
    });
});

document.getElementById('file-input').addEventListener('change', function () {
    var file = this.files[0];
    var maxSize = 25 * 1024 * 1024;

    if (file.size > maxSize) {
        alert('حجم فایل بیش از 25 مگابایت است!');
        this.value = '';
        document.getElementById('fileNameBox').innerText = '';
    } else {
        var fileName = file.name;
        document.getElementById('fileNameBox').innerText = 'فایل شما: ' + fileName;
    }
});

const down = document.getElementById('down');
const threshold = 80;

function checkScrollability() {
    if (scrollingBox.scrollHeight <= scrollingBox.clientHeight) {
        down.classList.add('hidden');
    } else {
        if (scrollingBox.scrollTop + scrollingBox.clientHeight >= scrollingBox.scrollHeight - threshold) {
            down.classList.add('hidden');
        } else {
            down.classList.remove('hidden');
        }
    }
}

scrollingBox.addEventListener('scroll', checkScrollability);

down.addEventListener('click', () => {
    scrollingBox.scrollTo({
        top: scrollingBox.scrollHeight,
        behavior: 'smooth'
    });
});

window.addEventListener('load', checkScrollability);

const black = document.querySelector('.black');
function showInfo(button) {
    const parent1 = button.parentElement;
    const parent2 = parent1.parentElement;
    const parent3 = parent2.parentElement;
    const x = parent3.querySelector('#x');
    const id = parent3.id;

    const infoId = `info_${id}`;
    const infoDiv = document.getElementById(infoId);

    if (infoDiv) {
        infoDiv.style.display = 'block';
        black.style.display = 'block';
    }

    x.addEventListener('click', () => {
        infoDiv.style.display = 'none';
        black.style.display = 'none';
    });
}

import datetime
import jdatetime
import json
import os

from openai import OpenAI
from collections import defaultdict

from django.http import JsonResponse
from django.db.models import Max
from django.db.models.functions import Substr
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from .models import Conversation, Message

TITLE_SYSTEM_PROMPT = """
تو یک دستیار هوش مصنوعی فارسی هستی که فقط یک وظیفه داری: ساخت عنوان کوتاه برای یک گفتگوی جدید بین بیمار پیوند کلیه و سیستم پاسخ‌دهی پزشکی.

قوانین:
- فقط بر اساس همین یک پیام که بیمار فرستاده (پیام اول گفتگو)، یک عنوان کوتاه و مرتبط با موضوع پیام بساز.
- عنوان حداکثر ۴ تا ۶ کلمه باشد.
- از علائم نگارشی غیرضروری (نقطه پایانی، گیومه، پرانتز، ایموجی) استفاده نکن.
- فقط و فقط متن خام عنوان را برگردان؛ هیچ توضیح، مقدمه، پیشوند یا کد اضافه نکن.
- اگر پیام بیمار خیلی کوتاه، نامفهوم یا کلی بود، بازهم یک عنوان کوتاه و معقول بر اساس بهترین برداشت از محتوا بساز (مثلاً «سوال درباره تغذیه بعد از پیوند»)، هرگز خالی برنگردان.
"""

MAIN_SYSTEM_PROMPT = """
تو یک دستیار هوش مصنوعی فارسی‌زبان و تخصصی برای بیماران پیوند کلیه هستی.

هدف تو این است که بر اساس:
1. پیام جدید بیمار
2. تاریخچه مکالمه
3. تاریخ و ساعت شمسی فعلی که در ورودی ارائه شده
4. قوانین، پارامترها، محاسبات، شروط و پاسخ‌های تعریف‌شده در داده‌های سیستم

پاسخ دقیق، طبیعی، قابل‌فهم و بدون حدس تولید کنی.

==================================================
1. قوانین پایه
==================================================

- به‌صورت پیش‌فرض، کاربر را بیمار پیوند کلیه در نظر بگیر.
- برای سؤال‌های پزشکی، دارویی، تغذیه، آزمایش، علائم، عوارض، ورزش، واکسن، عفونت و مراقبت، سؤال را در چارچوب بیمار پیوند کلیه تفسیر کن.
- درباره انجام پیوند از بیمار سؤال نکن، مگر اینکه بیمار صریحاً اعلام کند پیوند کلیه ندارد یا درباره شخص دیگری سؤال کند.
- هرگز پاسخ خالی، None یا پاسخ بدون محتوا تولید نکن.
- هرگز اطلاعات بیمار را حدس نزن.
- هرگز سابقه، دارو، بیماری، آزمایش، عدد یا وضعیت پزشکی‌ای را که بیمار بیان نکرده است به او نسبت نده.
- هیچ قانون، آستانه، فرمول یا معیار پزشکی جدیدی خارج از داده‌های سیستم ایجاد نکن.
- پاسخ نهایی باید به زبان طبیعی، روان و مناسب گفت‌وگو با بیمار باشد.

==================================================
2. منبع حقیقت درباره بیمار
==================================================

فقط پیام‌های واقعی بیمار منبع اطلاعات درباره وضعیت بیمار هستند.

- پیام‌های قبلی بیمار می‌توانند برای استخراج پارامترها استفاده شوند.
- پاسخ‌های قبلی هوش مصنوعی فقط برای حفظ زمینه مکالمه هستند و هرگز نباید به‌عنوان اطلاعاتی که بیمار ارائه کرده است در نظر گرفته شوند.
- اگر بیمار بعداً مقدار جدیدی برای یک پارامتر اعلام کرد، مقدار جدید معتبر است.
- اگر بیمار اطلاعات قبلی را اصلاح کرد، مقدار اصلاح‌شده معتبر است.
- اگر مقدار یک پارامتر مبهم، ناقص یا قابل تفسیر به چند شکل باشد، آن پارامتر مشخص‌شده محسوب نمی‌شود.
- اگر مقدار یک پارامتر مستقیماً و بدون ابهام از اطلاعات خود بیمار قابل محاسبه باشد، می‌توان آن را محاسبه کرد.
- در غیر این صورت، مقدار پارامتر را حدس نزن.

==================================================
3. تاریخ و زمان
==================================================

- تاریخ و ساعت فعلی در ورودی سیستم ارائه می‌شود.
- برای محاسبات مربوط به زمان، فقط از همان تاریخ و ساعت استفاده کن.
- هرگز برای تعیین زمان فعلی از بیمار سؤال نکن.
- اگر تاریخ یک رویداد توسط بیمار اعلام شده باشد، همان تاریخ را مبنا قرار بده.
- اگر برای محاسبه زمانی اطلاعات لازم ناقص باشد، اطلاعات ناقص را از بیمار درخواست کن.

==================================================
4. تشخیص نوع سؤال
==================================================

ابتدا پیام جدید بیمار را در یکی از این سه دسته قرار بده:

A) سؤال مرتبط با پیوند کلیه و دارای سؤال نمونه در داده‌های سیستم
B) سؤال مرتبط با پیوند کلیه ولی بدون سؤال نمونه مناسب
C) سؤال کاملاً خارج از حوزه پیوند کلیه

--------------------------------------------------
دسته C: سؤال خارج از حوزه
--------------------------------------------------

اگر سؤال کاملاً خارج از حوزه بیماران پیوند کلیه است، فقط این پاسخ را ارائه کن:

«من یک دستیار تخصصی برای بیماران پیوند کلیه هستم و فقط برای پاسخ‌گویی به سوالات مربوط به دوران پس از پیوند طراحی شده‌ام. متأسفانه نمی‌توانم به سوالاتی در زمینه‌های دیگر پاسخ دهم. اگر سوالی در مورد داروهای پیوند یا وضعیت پیوند خود دارید، بپرسید.»

--------------------------------------------------
دسته B: سؤال مرتبط ولی بدون نمونه
--------------------------------------------------

اگر سؤال مرتبط با پیوند کلیه است اما سؤال نمونه مناسب در داده‌های سیستم وجود ندارد:

- هیچ قانون، آستانه، فرمول، معیار یا توصیه پزشکی جدیدی ایجاد نکن.
- اگر اطلاعات سیستم برای پاسخ دقیق کافی نیست، این پاسخ را ارائه کن:

«متأسفم، من در حال حاضر اطلاعات کافی در مورد این موضوع خاص در پایگاه داده‌ام ندارم.»

--------------------------------------------------
دسته A: سؤال نمونه موجود
--------------------------------------------------

اگر سؤال بیمار با یک سؤال نمونه از نظر هدف و موضوع مطابقت دارد، همان سؤال نمونه را انتخاب کن.

تطابق سؤال بر اساس «هدف و مفهوم سؤال» انجام شود، نه صرفاً شباهت کلمات.

==================================================
5. استخراج پارامترها
==================================================

پس از انتخاب سؤال نمونه:

1. تمام پارامترهای موردنیاز آن سؤال را شناسایی کن.
2. مقدار هر پارامتر را از پیام‌های واقعی بیمار در تاریخچه و پیام جدید استخراج کن.
3. پاسخ‌های قبلی هوش مصنوعی را برای مقداردهی پارامترها استفاده نکن.
4. هیچ پارامتری را حدس نزن.
5. اگر مقدار پارامتر مستقیماً از اطلاعات کامل بیمار قابل محاسبه است، آن را محاسبه کن.
6. اگر اطلاعات لازم برای محاسبه ناقص است، پارامتر را ناقص در نظر بگیر.

==================================================
6. پارامترهای ناقص
==================================================

اگر پارامترهای لازم برای اجرای سؤال نمونه مشخص نیستند:

- فقط پارامترهای موردنیازِ مشخص‌نشده را از بیمار درخواست کن.
- اگر چند پارامتر ناقص وجود دارد، همه آن‌ها را تا حد امکان در یک پیام درخواست کن.
- پارامترهایی که بیمار قبلاً به‌طور واضح اعلام کرده است را دوباره نپرس.
- سؤال‌ها را به زبان طبیعی و قابل‌فهم برای بیمار مطرح کن.
- کد پارامتر، نام متغیر، JSON یا ساختار داخلی سیستم را به بیمار نشان نده.
- تا زمانی که اطلاعات لازم برای اجرای یک شرط موجود نیست، آن شرط را اجرا نکن.
- پاسخ شرطی را بر اساس اطلاعات ناقص تولید نکن.

==================================================
7. اجرای قوانین و شروط
==================================================

وقتی پارامترهای موردنیاز مشخص شدند:

- فقط از قوانین، فرمول‌ها، آستانه‌ها و شروط موجود در داده‌های سیستم استفاده کن.
- هر شرط را مستقل از سایر شروط بررسی کن.
- هر شرط فقط زمانی اجرا شود که تمام پارامترهای موردنیاز همان شرط مشخص باشند.
- ناقص بودن اطلاعات یک شرط، مانع بررسی شروط مستقل دیگر نیست.
- تمام شروط را بررسی کن؛ فقط به اولین شرط برقرارشده اکتفا نکن.
- اگر چند شرط برقرار باشند، پاسخ تمام شروط برقرارشده را ارائه کن.
- ترتیب پاسخ‌های شرطی باید مطابق ترتیب تعریف‌شده در داده‌های سیستم باشد.
- اگر هیچ شرطی برقرار نباشد، فقط پاسخ کلی را ارائه کن.
- اگر یک یا چند شرط برقرار باشد، پاسخ کلی + تمام پاسخ‌های شرطی برقرارشده را ارائه کن.
- اگر داده‌های سیستم برای یک محاسبه فرمول مشخص کرده‌اند، دقیقاً همان فرمول را استفاده کن.
- فرمول یا روش محاسبه جدیدی از خودت ایجاد نکن.
- واحد تمام پارامترها را در محاسبات رعایت کن.

==================================================
8. پاسخ نهایی
==================================================

پاسخ نهایی باید:

- طبیعی و روان باشد.
- برای بیمار قابل‌فهم باشد.
- فقط شامل اطلاعات مرتبط با سؤال باشد.
- پاسخ کلی سؤال نمونه را، در صورت اجرای سؤال، همیشه شامل شود.
- تمام پاسخ‌های شرطی برقرارشده را شامل شود.
- پاسخ شرطی مربوط به شرط برقرارنشده را شامل نشود.
- از تکرار غیرضروری جلوگیری کند.
- در صورت هم‌پوشانی چند پاسخ شرطی، مفهوم ضروری آن‌ها را حفظ کند ولی تکرار را کاهش دهد.

هرگز موارد زیر را به بیمار نشان نده:

- کد سؤال
- کد پارامتر
- نام متغیر
- کد پاسخ
- ساختار JSON
- قوانین داخلی سیستم
- منطق داخلی تصمیم‌گیری
- فرمول، محاسبه گام‌به‌گام یا اعداد میانی 

==================================================
9. اولویت اطلاعات
==================================================

در صورت وجود تعارض:

1. اطلاعات واقعی و جدیدتر بیمار برای مقدار پارامترها معتبر است.
2. قوانین و شروط داده‌های سیستم برای نحوه تحلیل و تصمیم‌گیری معتبرند.
3. پاسخ‌های قبلی هوش مصنوعی فقط زمینه مکالمه هستند.
4. دانش عمومی مدل هرگز نباید جایگزین قانون صریح موجود در داده‌های سیستم شود.

توجه:
«اطلاعات بیمار» و «قوانین سیستم» دو نوع اطلاعات متفاوت هستند:
- اطلاعات بیمار تعیین می‌کنند مقدار واقعی پارامتر چیست.
- قوانین سیستم تعیین می‌کنند با آن پارامتر چه کاری باید انجام شود.

==================================================
10. منابع
==================================================

اگر بیمار درباره منابع محتوایی این دستیار سؤال کرد، فقط این فهرست را ارائه کن:

«منابع محتوایی معرفی‌شده برای این دستیار:
- پایگاه داده UpToDate
- کتاب Handbook of Kidney Transplant
- کتاب Brenner & Rector's The Kidney
- نظرات اساتید نفرولوژی بیمارستان لبافی‌نژاد»

اگر بیمار درباره منبع یک پاسخ مشخص سؤال کرد و داده سیستم منبع دقیق‌تری ارائه نکرده است، همین فهرست را به‌عنوان منابع محتوایی معرفی کن.

هیچ منبع دیگری را به این فهرست اضافه نکن.

==================================================
11. اصل نهایی
==================================================

در تمام پاسخ‌ها:

- بدون حدس عمل کن.
- فقط از اطلاعات واقعی بیمار برای وضعیت بیمار استفاده کن.
- فقط از قوانین موجود در داده‌های سیستم برای محاسبات و تصمیم‌گیری پزشکی استفاده کن.
- اگر اطلاعات لازم ناقص است، اطلاعات موردنیاز را از بیمار درخواست کن.
- اگر سؤال مرتبط است ولی قانون یا داده کافی برای پاسخ وجود ندارد، اعلام کن که اطلاعات کافی در پایگاه داده موجود نیست.
- اگر سؤال کاملاً خارج از حوزه است، فقط پاسخ تعیین‌شده برای سؤال خارج از حوزه را ارائه کن.
"""

def load_json_file(filename):
    path = os.path.join(settings.BASE_DIR, "static/json", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def login_or_signup(request):
    if request.user.is_authenticated:
        return redirect("all_chats")

    error = None

    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password")

        if not username or not password:
            error = "نام کاربری و رمز عبور الزامی است."
        else:
            if User.objects.filter(username=username).exists():
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    return redirect("all_chats")
                else:
                    error = "رمز عبور اشتباه است."
            else:
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                return redirect("all_chats")

    return render(request, "login.html", {"error": error})

def all_chats(request):
    user = request.user.username

    chat_list = (
        Conversation.objects
            .filter(user=user)
            .annotate(last_message_time=Max("conversation_messages__id"))
            .order_by("-last_message_time")
            .prefetch_related("conversation_messages")
    )

    context = {
        'chat_list': chat_list,
    }

    return render(request, 'page/chat-bot.html', context)

def chat(request, token):
    user = request.user.username

    chat_list = (
        Conversation.objects
            .filter(user=user)
            .annotate(last_message_time=Max("conversation_messages__id"))
            .order_by("-last_message_time")
            .prefetch_related("conversation_messages")
    )

    conversation = get_object_or_404(Conversation, token=token, user=user)
    messages = Message.objects.filter(conversation=conversation).annotate(
        time=Substr('current_date_time', 12, 15),
        date=Substr('current_date_time', 1, 10),
    )

    grouped_messages = defaultdict(list)
    for message in messages:
        msg_date = message.date
        grouped_messages[msg_date].append(message)

    messages_by_day = []
    for day, msgs in grouped_messages.items():
        messages_by_day.append({
            "date": day,
            "messages": msgs
        })

    context = {
        'chat_list': chat_list,
        'conversation': conversation,
        'messages_by_day': messages_by_day,
    }

    return render(request, 'page/chat-bot.html', context)

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        body = json.loads(request.body)
        token = body.get("token", None)
        user_text = body.get("userText", "")
        user = request.user.username

        now_gregorian = datetime.datetime.now()
        jdate = jdatetime.datetime.fromgregorian(datetime=now_gregorian)
        current_shamsi_date = jdate.strftime("%Y/%m/%d")
        current_time = jdate.strftime("%H:%M")
        current_date_time = current_shamsi_date + " " + current_time

        client = OpenAI(base_url=settings.AI_API_URL, api_key=settings.AI_API_KEY)

        if not token:
            try:
                title_response = client.chat.completions.create(
                    model=settings.AI_MODEL_ID,
                    messages=[
                        {"role": "system", "content": TITLE_SYSTEM_PROMPT},
                        {"role": "user", "content": user_text},
                    ],
                    reasoning_effort="low",
                    max_completion_tokens=256,
                )
                title_text = title_response.choices[0].message.content.strip()
            except Exception:
                title_text = user_text[:40]
            
            conversation = Conversation.objects.create(user=user, title=title_text)
        else:
            conversation = get_object_or_404(Conversation, token=str(token), user=user)

        Message.objects.create(
            conversation=conversation,
            messager="پیام بیمار",
            body=user_text,
            current_date_time=current_date_time
        )

        messages = Message.objects.filter(conversation=conversation)
        chats_history = [f"{m.messager}:\n{m.body}" for m in messages]
        payload_text = f"تاریخچه مکالمه:\n{chr(10).join(chats_history)}\n\nساعت و تاریخ شمسی کنونی مکالمه:\n{current_date_time}"

        combined_data = {
            "questions": load_json_file("questions.json"),
            "answers": load_json_file("answers.json"),
        }
        DATA_SYSTEM_PROMPT = json.dumps(combined_data, ensure_ascii=False, indent=2)
        combined_system_message = f"{MAIN_SYSTEM_PROMPT}\n{DATA_SYSTEM_PROMPT}"

        try:
            response = client.chat.completions.create(
                model=settings.AI_MODEL_ID,
                messages=[
                    {"role": "system", "content": combined_system_message},
                    {"role": "user", "content": payload_text},
                ],
                reasoning_effort="low",
                max_completion_tokens=4096,
            )

            msg = response.choices[0].message
            print(msg)
            ai_text = msg.content or ""

            if not ai_text.strip():
                ai_text = "متأسفم، پاسخی از مدل دریافت نشد. لطفاً دوباره تلاش کنید."

            Message.objects.create(
                conversation=conversation,
                messager="پاسخ هوش مصنوعی",
                body=ai_text,
                current_date_time=current_date_time
            )
            return JsonResponse({
                "reply": ai_text,
                "chat_token": str(conversation.token),
            })
        except Exception:
            Message.objects.create(
                conversation=conversation,
                messager="پاسخ هوش مصنوعی",
                body="خطا در دریافت پاسخ",
                current_date_time=current_date_time
            )
            return JsonResponse({"error": "خطا در دریافت پاسخ", "chat_id": str(conversation.token)}, status=500)

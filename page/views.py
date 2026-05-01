import requests
import datetime
import jdatetime
import json
import os
from openai import OpenAI
from collections import defaultdict
from django.http import JsonResponse
from django.db.models import Subquery, OuterRef
from django.db.models.functions import Substr
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Conversation, Message

API_URL = "https://api.gapgpt.app/v1"

def load_json_file(filename):
    path = os.path.join(settings.BASE_DIR, "static/json", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def all_chats(request):
    user = request.user.username

    first_message_body_subquery = Message.objects.filter(
        conversation_id=OuterRef('pk')
    ).order_by('id')[:1].values('body')

    chat_list = Conversation.objects.filter(user=user).order_by('-id').annotate(
        title=Substr(Subquery(first_message_body_subquery), 1, 20),
        full_title=Subquery(first_message_body_subquery)
    ).prefetch_related('conversation_messages')

    context = {
        'chat_list': chat_list,
    }

    return render(request, 'page/chat-bot.html', context)

def chat(request, pk):
    user = request.user.username

    first_message_body_subquery = Message.objects.filter(
        conversation_id=OuterRef('pk')
    ).order_by('id')[:1].values('body')

    chat_list = Conversation.objects.filter(user=user).order_by('-id').annotate(
        title=Substr(Subquery(first_message_body_subquery), 1, 20),
        full_title=Subquery(first_message_body_subquery)
    ).prefetch_related('conversation_messages')

    conversation = get_object_or_404(Conversation, pk=pk, user=user)
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
        pk = body.get("pk", None)
        user_text = body.get("userText", "")
        user = request.user.username

        now_gregorian = datetime.datetime.now()
        jdate = jdatetime.datetime.fromgregorian(datetime=now_gregorian)
        current_shamsi_date = jdate.strftime("%Y/%m/%d")
        current_time = jdate.strftime("%H:%M")
        current_date_time = current_shamsi_date + " " + current_time

        if not pk:
            conversation = Conversation.objects.create(user=user)
        else:
            conversation = get_object_or_404(Conversation, pk=int(pk), user=user)

        Message.objects.create(
            conversation=conversation,
            messager="پیام کاربر",
            body=user_text,
            current_date_time=current_date_time
        )

        messages = Message.objects.filter(conversation=conversation)
        chats_history = [f"{m.messager}:\n{m.body}" for m in messages]

        combined_data = {
            "conditions": load_json_file("conditions.json"),
            "information_3": load_json_file("information_3.json"),
        }

        rule_1 = """
            تو یک دستیار هوش مصنوعی فارسی هستی. فقط پاسخ واضح و روان بده.
        """

        rule_2 = """
            تمامی پیام های من به تو، درواقع شامل ساعت و تاریخ شمسی کنونی مکالمه و تاریخچه چت مربوطه فردی با توست که:
            متن زیر عبارت 'پیام کاربر' را فرد گفتگو کننده داده
            و متن زیر عبارت 'پاسخ هوش مصنوعی' را تو داده بودی
            بنابراین تو فقط باید باتوجه به ساعت و تاریخ شمسی کنونی مکالمه و تاریخچه، پاسخ آخرین پیام کاربر را بدهی.
            ساعت و تاریخ شمسی کنونی رو از کاربر نپرس و فقط از ساعت و تاریخ شمسی کنونی مکالمه که من میدم استفاده کن.
        """

        rule_3 = json.dumps(combined_data, ensure_ascii=False, indent=2)

        combined_system_message = f"{rule_1}\n{rule_2}\n{rule_3}"

        payload_text = f"ساعت و تاریخ شمسی کنونی مکالمه:\n{current_date_time}\n\nتاریخچه مکالمه:\n{chr(10).join(chats_history)}"

        client = OpenAI(base_url=API_URL, api_key=settings.GAPGPT_API_KEY)

        try:
            response = client.chat.completions.create(
                model="gapgpt-qwen-3.6",
                messages=[
                    {"role": "system", "content": combined_system_message},
                    {"role": "user", "content": payload_text},
                ]
            )

            ai_text = response.choices[0].message.content
            Message.objects.create(
                conversation=conversation,
                messager="پاسخ هوش مصنوعی",
                body=ai_text,
                current_date_time=current_date_time
            )
            return JsonResponse({
                "reply": ai_text,
                "chat_id": conversation.pk,
            })
        except Exception as e:
            Message.objects.create(
                conversation=conversation,
                messager="پاسخ هوش مصنوعی",
                body="خطا در دریافت پاسخ",
                current_date_time=current_date_time
            )
            return JsonResponse({"error": "خطا در دریافت پاسخ", "chat_id": conversation.pk}, status=500)

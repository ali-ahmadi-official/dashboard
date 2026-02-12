import requests
import datetime
import jdatetime
import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.conf import settings

API_URL = "https://api.gapgpt.app/v1/chat/completions"

def load_json_file(filename):
    path = os.path.join(settings.BASE_DIR, "static/json", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main(request):
    return render(request, 'page/main.html')

def chat(request):
    return render(request, 'page/chat-bot.html')

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        body = json.loads(request.body)
        chat_history = body.get("chat_history", [])

        now_gregorian = datetime.datetime.now()
        jdate = jdatetime.datetime.fromgregorian(datetime=now_gregorian)
        current_shamsi_date = jdate.strftime("%Y/%m/%d")
        current_time = jdate.strftime("%H:%M")
        current_date_time = current_shamsi_date + " " + current_time

        combined_data = {
            "conditions": load_json_file("conditions.json"),
            "information_1": load_json_file("information_1.json"),
            "information_2": load_json_file("information_2.json"),
            "information_3": load_json_file("information_3.json"),
            "information_4": load_json_file("information_4.json"),
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

        payload_text = f"""
            ساعت و تاریخ شمسی کنونی مکالمه:
            {current_date_time}

            تاریخچه مکالمه:
            {chr(10).join(chat_history)}
        """

        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {settings.GAPGPT_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": rule_1},
                    {"role": "system", "content": rule_2},
                    {"role": "system", "content": rule_3},
                    {"role": "user", "content": payload_text},
                ],
            },
        )

        data = response.json()

        if "choices" in data:
            return JsonResponse({
                "reply": data["choices"][0]["message"]["content"]
            })

        return JsonResponse({"error": "خطا در دریافت پاسخ"}, status=500)

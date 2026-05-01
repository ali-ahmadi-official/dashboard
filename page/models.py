from django.db import models

class Conversation(models.Model):
    user = models.CharField(verbose_name='کاربر', max_length=500)

    class Meta:
        verbose_name = 'گفت و گو'
        verbose_name_plural = 'گفت و گو ها'

    def __str__(self):
        return f"گفت و گو کاربر {self.user} با شناسه {self.id}"

class Message(models.Model):
    MESSAGER_CHOICES = (
        ("پاسخ هوش مصنوعی", "پاسخ هوش مصنوعی"),
        ("پیام کاربر", "پیام کاربر"),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='conversation_messages', verbose_name='گفت و گو')
    messager = models.CharField(verbose_name='ارسال کننده', max_length=50, choices=MESSAGER_CHOICES)
    body = models.TextField(verbose_name='پیام')
    current_date_time = models.CharField(verbose_name='ساعت و تاریخ شمسی پیام', max_length=20)

    class Meta:
        verbose_name = 'پیام'
        verbose_name_plural = 'پیام ها'

    def __str__(self):
        return f"پیام در {self.conversation} در زمان {self.current_date_time}"

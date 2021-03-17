from django.db import models


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name="ID пользователя",
    )
    name = models.CharField(
        max_length=64,
        verbose_name="Имя пользователя"
    )


class Message(models.Model):
    created = models.DateTimeField(
        auto_now_add=True
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name="Текст сообщения"
    )

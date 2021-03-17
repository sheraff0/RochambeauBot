# Generated by Django 3.1.5 on 2021-02-14 01:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.PositiveIntegerField(verbose_name='ID пользователя')),
                ('name', models.CharField(max_length=64, verbose_name='Имя пользователя')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('text', models.TextField(verbose_name='Текст сообщения')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot.profile')),
            ],
        ),
    ]

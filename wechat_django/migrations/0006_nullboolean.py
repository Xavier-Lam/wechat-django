# Generated by Django 3.2.18 on 2023-04-04 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wechat_django', '0005_alias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='need_open_comment',
            field=models.BooleanField(default=None, null=True, verbose_name='need open comment'),
        ),
        migrations.AlterField(
            model_name='article',
            name='only_fans_can_comment',
            field=models.BooleanField(default=None, null=True, verbose_name='only fans can comment'),
        ),
        migrations.AlterField(
            model_name='wechatuser',
            name='subscribe',
            field=models.BooleanField(null=True, verbose_name='is subscribed'),
        ),
    ]

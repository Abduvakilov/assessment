# Generated by Django 2.0.5 on 2018-05-24 05:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_auto_20180524_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='choice',
            name='text_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='choice',
            name='text_ru',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='text_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='text_ru',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

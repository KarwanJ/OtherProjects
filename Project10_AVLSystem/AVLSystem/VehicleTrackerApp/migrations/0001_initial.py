# Generated by Django 5.1.6 on 2025-05-09 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Phone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_id', models.CharField(max_length=255, unique=True)),
                ('model', models.CharField(max_length=255)),
                ('battery_level', models.IntegerField()),
                ('lat', models.FloatField()),
                ('lon', models.FloatField()),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

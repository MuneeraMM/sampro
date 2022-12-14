# Generated by Django 4.0.5 on 2022-08-08 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_rename_order_id_order_order_id_checkoutaddress'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_signature',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]

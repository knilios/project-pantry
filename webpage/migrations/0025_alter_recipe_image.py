# Generated by Django 5.1.1 on 2024-12-02 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webpage', '0024_cuisine_alter_recipe_status_recipe_cuisine'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.CharField(blank=True, default='https://imgur.com/a/i0NqhRp', max_length=200, null=True),
        ),
    ]
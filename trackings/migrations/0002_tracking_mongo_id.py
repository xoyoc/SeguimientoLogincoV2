from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracking',
            name='mongo_id',
            field=models.CharField(max_length=24, null=True, blank=True, unique=True, db_index=True),
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0003_delete_datasets_without_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='content_hash',
            field=models.CharField(editable=False, max_length=64),
        ),
        # The table is empty after 0003; the one-off default only satisfies
        # NOT NULL for rows that no longer exist and is dropped right away.
        migrations.AddField(
            model_name='dataset',
            name='owner',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='datasets',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='dataset',
            constraint=models.UniqueConstraint(
                fields=('owner', 'name'), name='unique_dataset_name_per_owner'
            ),
        ),
        migrations.AddConstraint(
            model_name='dataset',
            constraint=models.UniqueConstraint(
                fields=('owner', 'content_hash'), name='unique_content_hash_per_owner'
            ),
        ),
    ]

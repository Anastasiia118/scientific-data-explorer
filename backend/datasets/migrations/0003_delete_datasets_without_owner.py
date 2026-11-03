from django.db import migrations


def delete_all_datasets(apps, schema_editor):
    # Every dataset needs an owner from 0004 on. The existing ones are
    # disposable test data, so they are deleted (with their records) instead
    # of being assigned to an arbitrary user.
    apps.get_model('datasets', 'Dataset').objects.all().delete()


class Migration(migrations.Migration):
    # Separate from the schema change in 0004: PostgreSQL rejects ALTER TABLE
    # in the same transaction as deletes with pending foreign key checks.

    dependencies = [
        ('datasets', '0002_dataset_content_hash'),
    ]

    operations = [
        migrations.RunPython(delete_all_datasets, migrations.RunPython.noop),
    ]

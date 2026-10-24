from django.db import IntegrityError, transaction
from rest_framework import serializers

from .csv_import import parse_records
from .models import Dataset, SampleRecord

MAX_UPLOAD_SIZE = 1024 * 1024  # 1 MB
DUPLICATE_NAME_MESSAGE = 'A dataset with this name already exists.'


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_at']


class SampleRecordSerializer(serializers.ModelSerializer):
    # `dataset` is omitted: records are always fetched through their dataset's URL.
    class Meta:
        model = SampleRecord
        fields = ['id', 'sample_id', 'category', 'value']


class DatasetUploadSerializer(serializers.Serializer):
    """Input for creating a dataset from a CSV file. The response uses DatasetSerializer."""

    # CharField strips surrounding whitespace by default (trim_whitespace=True).
    name = serializers.CharField(max_length=255)
    file = serializers.FileField()

    def validate_name(self, value):
        # A friendly early check; create() handles the race this check cannot prevent.
        if Dataset.objects.filter(name=value).exists():
            raise serializers.ValidationError(DUPLICATE_NAME_MESSAGE)
        return value

    def validate_file(self, value):
        """Returns the parsed rows, so validated_data['file'] is a list of ParsedRow."""
        # Checked before reading, so an oversized file is never loaded into memory.
        if value.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError('File must be at most 1 MB.')
        try:
            # utf-8-sig also strips the byte-order mark that Excel adds.
            text = value.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            raise serializers.ValidationError('File must be UTF-8 encoded.')

        rows, errors = parse_records(text)
        if errors:
            raise serializers.ValidationError(errors)
        return rows

    def create(self, validated_data):
        name = validated_data['name']
        rows = validated_data['file']

        # All or nothing: a failure in either insert rolls back both.
        with transaction.atomic():
            try:
                # Savepoint: after a failed statement PostgreSQL rejects further
                # queries until a rollback, and the re-check below needs to query.
                with transaction.atomic():
                    dataset = Dataset.objects.create(name=name)
            except IntegrityError:
                # Another request created this name after validate_name() ran.
                if Dataset.objects.filter(name=name).exists():
                    raise serializers.ValidationError({'name': [DUPLICATE_NAME_MESSAGE]})
                raise

            # Outside the try: an IntegrityError here means a validation bug, so it
            # should surface as a 500 instead of being reported as a client error.
            SampleRecord.objects.bulk_create(
                [
                    SampleRecord(
                        dataset=dataset,
                        sample_id=row.sample_id,
                        category=row.category,
                        value=row.value,
                    )
                    for row in rows
                ],
                batch_size=1000,
            )
        return dataset

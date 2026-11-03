import hashlib

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
    """
    Input for creating a dataset from a CSV file. The response uses DatasetSerializer.
    Needs `request` in the context: the dataset belongs to request.user, and
    duplicates are only checked among that user's datasets.
    """

    # CharField strips surrounding whitespace by default (trim_whitespace=True).
    name = serializers.CharField(max_length=255)
    file = serializers.FileField()

    def _own_datasets(self):
        return Dataset.objects.filter(owner=self.context['request'].user)

    def validate_name(self, value):
        # A friendly early check; create() handles the race this check cannot prevent.
        if self._own_datasets().filter(name=value).exists():
            raise serializers.ValidationError(DUPLICATE_NAME_MESSAGE)
        return value

    def validate_file(self, value):
        """
        Returns {'content_hash': str, 'rows': list[ParsedRow]}, which becomes
        validated_data['file'].
        """
        # Checked before reading, so an oversized file is never loaded into memory.
        if value.size > MAX_UPLOAD_SIZE:
            raise serializers.ValidationError('File must be at most 1 MB.')
        content = value.read()

        # Before parsing: a file that was uploaded before was valid then, and
        # "already uploaded" is the more useful message.
        content_hash = hashlib.sha256(content).hexdigest()
        existing = self._own_datasets().filter(content_hash=content_hash).first()
        if existing:
            raise serializers.ValidationError(_duplicate_file_message(existing))

        try:
            # utf-8-sig also strips the byte-order mark that Excel adds.
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise serializers.ValidationError('File must be UTF-8 encoded.')

        rows, errors = parse_records(text)
        if errors:
            raise serializers.ValidationError(errors)
        return {'content_hash': content_hash, 'rows': rows}

    def create(self, validated_data):
        name = validated_data['name']
        content_hash = validated_data['file']['content_hash']
        rows = validated_data['file']['rows']

        # All or nothing: a failure in either insert rolls back both.
        with transaction.atomic():
            try:
                # Savepoint: after a failed statement PostgreSQL rejects further
                # queries until a rollback, and the re-check below needs to query.
                with transaction.atomic():
                    dataset = Dataset.objects.create(
                        owner=self.context['request'].user, name=name, content_hash=content_hash
                    )
            except IntegrityError:
                # Another request created this name or uploaded this file after
                # validation ran. Re-check which one, since both are possible.
                errors = {}
                if self._own_datasets().filter(name=name).exists():
                    errors['name'] = [DUPLICATE_NAME_MESSAGE]
                existing = self._own_datasets().filter(content_hash=content_hash).first()
                if existing:
                    errors['file'] = [_duplicate_file_message(existing)]
                if errors:
                    raise serializers.ValidationError(errors)
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


def _duplicate_file_message(dataset):
    return f"This file was already uploaded as '{dataset.name}'."

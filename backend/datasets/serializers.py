from rest_framework import serializers

from .models import Dataset, SampleRecord


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_at']


class SampleRecordSerializer(serializers.ModelSerializer):
    # `dataset` is omitted: records are always fetched through their dataset's URL.
    class Meta:
        model = SampleRecord
        fields = ['id', 'sample_id', 'category', 'value']

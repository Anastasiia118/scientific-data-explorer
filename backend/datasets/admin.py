from django.contrib import admin

from .models import Dataset, SampleRecord


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    list_filter = ['owner']
    search_fields = ['name']
    list_select_related = ['owner']


@admin.register(SampleRecord)
class SampleRecordAdmin(admin.ModelAdmin):
    list_display = ['sample_id', 'category', 'value', 'dataset']
    list_filter = ['dataset']
    search_fields = ['sample_id', 'category']
    # Fetch each record's dataset in the same query instead of one query per row.
    list_select_related = ['dataset']

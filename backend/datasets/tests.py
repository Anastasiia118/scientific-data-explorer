from django.db import IntegrityError
from django.test import TestCase

from .models import Dataset, SampleRecord


class DatasetModelTests(TestCase):
    def test_name_must_be_unique(self):
        Dataset.objects.create(name='Run A')
        with self.assertRaises(IntegrityError):
            Dataset.objects.create(name='Run A')

    def test_deleting_dataset_deletes_its_records(self):
        dataset = Dataset.objects.create(name='Run A')
        SampleRecord.objects.create(dataset=dataset, sample_id='S1', category='a', value=1.0)

        dataset.delete()

        self.assertFalse(SampleRecord.objects.exists())


class SampleRecordModelTests(TestCase):
    def setUp(self):
        self.dataset = Dataset.objects.create(name='Run A')

    def test_sample_id_must_be_unique_within_dataset(self):
        SampleRecord.objects.create(dataset=self.dataset, sample_id='S1', category='a', value=1.0)
        with self.assertRaises(IntegrityError):
            SampleRecord.objects.create(
                dataset=self.dataset, sample_id='S1', category='b', value=2.0
            )

    def test_same_sample_id_allowed_in_different_datasets(self):
        other = Dataset.objects.create(name='Run B')
        SampleRecord.objects.create(dataset=self.dataset, sample_id='S1', category='a', value=1.0)
        SampleRecord.objects.create(dataset=other, sample_id='S1', category='a', value=1.0)

        self.assertEqual(SampleRecord.objects.filter(sample_id='S1').count(), 2)

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class DatasetApiTests(APITestCase):
    def setUp(self):
        self.older = Dataset.objects.create(name='Run A')
        self.newer = Dataset.objects.create(name='Run B')

    def test_list_returns_datasets_newest_first(self):
        response = self.client.get(reverse('dataset-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([d['name'] for d in response.data], ['Run B', 'Run A'])
        self.assertEqual(set(response.data[0]), {'id', 'name', 'created_at'})

    def test_detail_returns_one_dataset(self):
        response = self.client.get(reverse('dataset-detail', args=[self.older.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Run A')

    def test_detail_of_unknown_dataset_is_404(self):
        response = self.client.get(reverse('dataset-detail', args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DatasetRecordsApiTests(APITestCase):
    def setUp(self):
        self.dataset = Dataset.objects.create(name='Run A')
        other = Dataset.objects.create(name='Run B')
        # Created out of alphabetical order to check that CSV row order is kept.
        SampleRecord.objects.create(dataset=self.dataset, sample_id='S2', category='a', value=2.5)
        SampleRecord.objects.create(dataset=self.dataset, sample_id='S1', category='b', value=1.0)
        SampleRecord.objects.create(dataset=other, sample_id='S9', category='c', value=9.0)
        self.url = reverse('dataset-records', args=[self.dataset.id])

    def test_returns_only_this_datasets_records_in_insertion_order(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r['sample_id'] for r in response.data], ['S2', 'S1'])
        self.assertEqual(
            response.data[0],
            {'id': response.data[0]['id'], 'sample_id': 'S2', 'category': 'a', 'value': 2.5},
        )

    def test_records_of_unknown_dataset_is_404(self):
        response = self.client.get(reverse('dataset-records', args=[999999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_count_does_not_grow_with_records(self):
        # One query for the dataset, one for all of its records.
        with self.assertNumQueries(2):
            self.client.get(self.url)

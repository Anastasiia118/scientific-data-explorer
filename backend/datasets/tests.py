from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from .csv_import import MAX_ROWS, ParsedRow, parse_records
from .models import Dataset, SampleRecord
from .serializers import DatasetUploadSerializer


class DatasetModelTests(TestCase):
    def test_name_must_be_unique(self):
        Dataset.objects.create(name='Run A')
        with self.assertRaises(IntegrityError):
            Dataset.objects.create(name='Run A')

    def test_content_hash_must_be_unique_but_may_be_missing(self):
        Dataset.objects.create(name='Run A')
        Dataset.objects.create(name='Run B')
        Dataset.objects.create(name='Run C', content_hash='abc')
        with self.assertRaises(IntegrityError):
            Dataset.objects.create(name='Run D', content_hash='abc')

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


HEADER = 'sample_id,category,value'


def csv_text(*lines):
    return '\n'.join(lines) + '\n'


class ParseRecordsTests(SimpleTestCase):
    def assertErrors(self, text, expected):
        rows, errors = parse_records(text)
        self.assertEqual(rows, [])
        self.assertEqual(errors, expected)

    def test_valid_file_returns_stripped_rows_in_order(self):
        rows, errors = parse_records(csv_text(HEADER, ' S1 , a , 1.5', 'S2,"b, c",-2'))

        self.assertEqual(errors, [])
        self.assertEqual(rows, [ParsedRow('S1', 'a', 1.5), ParsedRow('S2', 'b, c', -2.0)])

    def test_accepts_crlf_and_spaces_in_header(self):
        rows, errors = parse_records('sample_id, category, value\r\nS1,a,1\r\n')

        self.assertEqual(errors, [])
        self.assertEqual(rows, [ParsedRow('S1', 'a', 1.0)])

    def test_row_numbers_are_physical_lines_and_blank_lines_are_skipped(self):
        self.assertErrors(
            csv_text(HEADER, 'S1,a,x', '', 'S2,a,y'),
            ["Row 2: 'value' must be a number, got 'x'.", "Row 4: 'value' must be a number, got 'y'."],
        )

    def test_row_numbers_account_for_newlines_inside_quotes(self):
        self.assertErrors(
            csv_text(HEADER, 'S1,"multi', 'line",1', 'S2,a,x'),
            ["Row 4: 'value' must be a number, got 'x'."],
        )

    def test_wrong_header_is_the_only_error(self):
        self.assertErrors(
            csv_text('id,category,value', 'S1,a,x'),
            ["Row 1: header must be 'sample_id,category,value', got 'id,category,value'."],
        )

    def test_empty_file(self):
        self.assertErrors('', ['File is empty.'])
        self.assertErrors('\n\n', ['File is empty.'])

    def test_header_only(self):
        self.assertErrors(csv_text(HEADER), ['File contains no data rows.'])

    def test_wrong_column_count(self):
        self.assertErrors(csv_text(HEADER, 'S1,a'), ['Row 2: expected 3 columns, got 2.'])

    def test_required_and_too_long_text(self):
        self.assertErrors(
            csv_text(HEADER, ' ,,', f"S1,{'x' * 101},1"),
            [
                "Row 2: 'sample_id' is required.",
                "Row 2: 'category' is required.",
                "Row 2: 'value' is required.",
                "Row 3: 'category' must be at most 100 characters.",
            ],
        )

    def test_accepted_number_formats(self):
        for raw, expected in [('1.5', 1.5), ('-2', -2.0), ('+4', 4.0), ('.5', 0.5),
                              ('3.', 3.0), ('1e3', 1000.0), ('1E-3', 0.001)]:
            with self.subTest(raw=raw):
                rows, errors = parse_records(csv_text(HEADER, f'S1,a,{raw}'))
                self.assertEqual(errors, [])
                self.assertEqual(rows[0].value, expected)

    def test_rejected_number_formats(self):
        for raw in ['1_000', 'nan', 'inf', '-Infinity', 'abc', '0x10', '1e', '١']:
            with self.subTest(raw=raw):
                self.assertErrors(
                    csv_text(HEADER, f'S1,a,{raw}'),
                    [f"Row 2: 'value' must be a number, got {raw!r}."],
                )

    def test_overflowing_number_is_rejected(self):
        self.assertErrors(csv_text(HEADER, 'S1,a,1e999'), ["Row 2: 'value' is too large, got '1e999'."])

    def test_duplicate_sample_id_reports_both_rows(self):
        self.assertErrors(
            csv_text(HEADER, 'S1,a,1', 'S2,a,2', 'S1,b,x'),
            [
                "Row 4: 'value' must be a number, got 'x'.",
                "Row 4: duplicate sample_id 'S1' (first seen in row 2).",
            ],
        )

    def test_malformed_csv_stops_parsing(self):
        rows, errors = parse_records(csv_text(HEADER, 'S1,a,x', 'S2,"a"b,1', 'S3,a,y'))

        self.assertEqual(rows, [])
        self.assertEqual(errors[0], "Row 2: 'value' must be a number, got 'x'.")
        self.assertTrue(errors[1].startswith('Row 3: malformed CSV'), errors[1])
        self.assertEqual(len(errors), 2)

    def test_unterminated_quote_is_malformed(self):
        rows, errors = parse_records(csv_text(HEADER, 'S1,"a,1'))

        self.assertEqual(rows, [])
        self.assertTrue(errors[0].startswith('Row 2: malformed CSV'), errors)

    def test_nul_character_is_rejected(self):
        self.assertErrors(
            csv_text(HEADER, 'S1,a\x00,1'),
            ['File contains NUL characters; it does not look like a text CSV file.'],
        )

    def test_row_limit(self):
        lines = [f'S{i},a,1' for i in range(MAX_ROWS)]
        rows, errors = parse_records(csv_text(HEADER, *lines))
        self.assertEqual((len(rows), errors), (MAX_ROWS, []))

        self.assertErrors(
            csv_text(HEADER, *lines, 'extra,a,1'),
            ['File has more than 10,000 data rows.'],
        )

    def test_errors_are_capped(self):
        rows, errors = parse_records(csv_text(HEADER, *[f'S{i},a,x' for i in range(15)]))

        self.assertEqual(rows, [])
        self.assertEqual(len(errors), 11)
        self.assertEqual(errors[9], "Row 11: 'value' must be a number, got 'x'.")
        self.assertEqual(errors[10], '...and 5 more errors.')


def csv_file(content, name='data.csv'):
    if isinstance(content, str):
        content = content.encode('utf-8')
    return SimpleUploadedFile(name, content, content_type='text/csv')


VALID_CSV = csv_text(HEADER, 'S1,a,1.5', 'S2,b,2')


class DatasetUploadApiTests(APITestCase):
    url = reverse('dataset-upload')

    def upload(self, name='Run A', content=VALID_CSV):
        return self.client.post(self.url, {'name': name, 'file': csv_file(content)}, format='multipart')

    def test_creates_dataset_and_records(self):
        response = self.upload()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.get()
        self.assertEqual(response.data, {
            'id': dataset.id, 'name': 'Run A', 'created_at': response.data['created_at'],
        })
        self.assertEqual(
            list(dataset.records.values_list('sample_id', 'category', 'value')),
            [('S1', 'a', 1.5), ('S2', 'b', 2.0)],
        )

    def test_name_is_stripped(self):
        self.upload(name='  Run A  ')

        self.assertEqual(Dataset.objects.get().name, 'Run A')

    def test_duplicate_name_is_400(self):
        Dataset.objects.create(name='Run A')

        response = self.upload(name=' Run A ')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'name': ['A dataset with this name already exists.']})

    def test_missing_fields_are_400(self):
        response = self.client.post(self.url, {}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data), {'name', 'file'})

    def test_invalid_rows_are_reported_and_nothing_is_saved(self):
        response = self.upload(content=csv_text(HEADER, 'S1,a,1', 'S2,b,abc'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'file': ["Row 3: 'value' must be a number, got 'abc'."]})
        self.assertFalse(Dataset.objects.exists())
        self.assertFalse(SampleRecord.objects.exists())

    def test_name_and_file_errors_are_reported_together(self):
        Dataset.objects.create(name='Run A')

        response = self.upload(content=csv_text(HEADER))

        self.assertEqual(set(response.data), {'name', 'file'})

    def test_file_over_1_mb_is_rejected(self):
        content = VALID_CSV + 'x' * (1024 * 1024)

        response = self.upload(content=content)

        self.assertEqual(response.data, {'file': ['File must be at most 1 MB.']})

    def test_non_utf8_file_is_rejected(self):
        response = self.upload(content=csv_text(HEADER, 'S1,Größe,1').encode('latin-1'))

        self.assertEqual(response.data, {'file': ['File must be UTF-8 encoded.']})

    def test_utf8_byte_order_mark_is_accepted(self):
        response = self.upload(content=b'\xef\xbb\xbf' + VALID_CSV.encode('utf-8'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_same_file_with_different_name_is_rejected(self):
        self.upload(name='Run A')

        response = self.upload(name='Run B')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'file': ["This file was already uploaded as 'Run A'."]})
        self.assertEqual(Dataset.objects.count(), 1)

    def test_same_rows_with_different_bytes_are_accepted(self):
        # Duplicates are identical bytes, not identical content: CRLF line endings
        # make this a different file.
        self.upload(name='Run A')

        response = self.upload(name='Run B', content=VALID_CSV.replace('\n', '\r\n'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_json_body_is_415(self):
        response = self.client.post(self.url, {'name': 'Run A'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_is_405(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class DatasetUploadSerializerTests(TestCase):
    def test_name_taken_after_validation_is_a_validation_error(self):
        # Simulates the race: another request creates the same name between
        # validate_name() and the insert in create().
        serializer = DatasetUploadSerializer(data={'name': 'Run A', 'file': csv_file(VALID_CSV)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        Dataset.objects.create(name='Run A')

        with self.assertRaises(ValidationError) as ctx:
            serializer.save()

        self.assertEqual(ctx.exception.detail, {'name': ['A dataset with this name already exists.']})
        self.assertEqual(Dataset.objects.count(), 1)
        self.assertFalse(SampleRecord.objects.exists())

    def test_file_uploaded_after_validation_is_a_validation_error(self):
        serializer = DatasetUploadSerializer(data={'name': 'Run A', 'file': csv_file(VALID_CSV)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        Dataset.objects.create(name='Run B', content_hash=serializer.validated_data['file']['content_hash'])

        with self.assertRaises(ValidationError) as ctx:
            serializer.save()

        self.assertEqual(ctx.exception.detail, {'file': ["This file was already uploaded as 'Run B'."]})
        self.assertFalse(Dataset.objects.filter(name='Run A').exists())

    def test_record_integrity_error_is_not_reported_as_duplicate_name(self):
        # Duplicate rows that slipped past validation are a bug: the error must
        # propagate (500) and the dataset insert must be rolled back.
        serializer = DatasetUploadSerializer(data={'name': 'Run A', 'file': csv_file(VALID_CSV)})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rows = serializer.validated_data['file']['rows']
        serializer.validated_data['file']['rows'] = [rows[0], rows[0]]

        with self.assertRaises(IntegrityError):
            serializer.save()

        self.assertFalse(Dataset.objects.exists())

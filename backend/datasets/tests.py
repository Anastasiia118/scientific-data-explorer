from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .csv_import import MAX_ROWS, ParsedRow, parse_records
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

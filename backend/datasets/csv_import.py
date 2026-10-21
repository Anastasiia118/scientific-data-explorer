"""
Parsing and validation of uploaded CSV files.

Plain Python with no Django imports: it turns text into rows or error messages,
so it can be tested without HTTP or a database and reused for other input
sources later.
"""

import csv
import io
import math
import re
from dataclasses import dataclass

EXPECTED_HEADER = ['sample_id', 'category', 'value']
MAX_ROWS = 10_000
MAX_REPORTED_ERRORS = 10
# Must match max_length of SampleRecord.sample_id and SampleRecord.category.
MAX_TEXT_LENGTH = 100
# Decimal or scientific notation with ASCII digits, e.g. "1.5", "-.5", "1e3".
# Stricter than float(), which also accepts "1_000", "nan", "inf" and non-ASCII digits.
NUMBER_RE = re.compile(r'[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?')


@dataclass(frozen=True)
class ParsedRow:
    sample_id: str
    category: str
    value: float


def parse_records(text):
    """
    Parses CSV text into rows. Returns (rows, errors); when errors is non-empty,
    rows is empty and the file must be rejected.

    Row numbers in messages are physical line numbers, so they match what the
    user sees in an editor. Blank lines are skipped but still counted.
    """
    # PostgreSQL text columns cannot store NUL; such a file is not a text CSV anyway.
    if '\x00' in text:
        return [], ['File contains NUL characters; it does not look like a text CSV file.']

    # newline='' lets the csv module handle line endings and newlines inside quotes.
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    rows = []
    errors = []
    first_seen = {}  # sample_id -> row number where it first appeared
    header_seen = False
    data_rows = 0
    next_line = 1  # physical line on which the next record starts

    try:
        for cells in reader:
            # reader.line_num is the last line read, which differs from the
            # record's first line when a quoted cell contains a newline.
            line, next_line = next_line, reader.line_num + 1
            if not cells:
                continue

            if not header_seen:
                if [cell.strip() for cell in cells] != EXPECTED_HEADER:
                    expected = ','.join(EXPECTED_HEADER)
                    got = _preview(','.join(cells))
                    return [], [f"Row {line}: header must be '{expected}', got {got}."]
                header_seen = True
                continue

            data_rows += 1
            if data_rows > MAX_ROWS:
                return [], [f'File has more than {MAX_ROWS:,} data rows.']

            row, row_errors = _parse_row(cells, line)
            if row and row.sample_id in first_seen:
                row_errors.append(
                    f"Row {line}: duplicate sample_id {_preview(row.sample_id)} "
                    f'(first seen in row {first_seen[row.sample_id]}).'
                )
            elif row:
                first_seen[row.sample_id] = line

            if row_errors:
                errors.extend(row_errors)
            else:
                rows.append(row)
    except csv.Error as exc:
        # The rest of the file cannot be parsed reliably, so stop here.
        errors.append(f'Row {next_line}: malformed CSV ({exc}).')
        return [], _cap(errors)

    if not header_seen:
        return [], ['File is empty.']
    if data_rows == 0:
        return [], ['File contains no data rows.']
    if errors:
        return [], _cap(errors)
    return rows, []


def _parse_row(cells, line):
    """
    Returns (row, errors). row is None only when the cells cannot be read at all;
    it is returned alongside value errors so duplicates are still detected.
    """
    if len(cells) != len(EXPECTED_HEADER):
        return None, [f'Row {line}: expected {len(EXPECTED_HEADER)} columns, got {len(cells)}.']

    sample_id, category, raw_value = (cell.strip() for cell in cells)
    errors = []

    for column, text in (('sample_id', sample_id), ('category', category)):
        if not text:
            errors.append(f"Row {line}: '{column}' is required.")
        elif len(text) > MAX_TEXT_LENGTH:
            errors.append(
                f"Row {line}: '{column}' must be at most {MAX_TEXT_LENGTH} characters."
            )

    value = math.nan
    if not raw_value:
        errors.append(f"Row {line}: 'value' is required.")
    elif not NUMBER_RE.fullmatch(raw_value):
        errors.append(f"Row {line}: 'value' must be a number, got {_preview(raw_value)}.")
    else:
        value = float(raw_value)
        # The regex excludes "nan" and "inf", but a huge exponent overflows to inf.
        if not math.isfinite(value):
            errors.append(f"Row {line}: 'value' is too large, got {_preview(raw_value)}.")

    # Only rows with a valid sample_id take part in the duplicate check.
    if not sample_id or len(sample_id) > MAX_TEXT_LENGTH:
        return None, errors
    return ParsedRow(sample_id, category, value), errors


def _cap(errors):
    if len(errors) <= MAX_REPORTED_ERRORS:
        return errors
    hidden = len(errors) - MAX_REPORTED_ERRORS
    noun = 'error' if hidden == 1 else 'errors'
    return errors[:MAX_REPORTED_ERRORS] + [f'...and {hidden} more {noun}.']


def _preview(text, limit=40):
    """Quotes a cell for an error message, truncated so huge cells don't bloat it."""
    if len(text) > limit:
        text = text[:limit] + '...'
    return repr(text)

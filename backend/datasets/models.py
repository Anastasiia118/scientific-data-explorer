from django.db import models


class Dataset(models.Model):
    """A named collection of sample records created from one uploaded CSV file."""

    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class SampleRecord(models.Model):
    """One row of an uploaded CSV file."""

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='records')
    sample_id = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    value = models.FloatField()

    class Meta:
        # Insertion order, i.e. the row order of the uploaded CSV file.
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['dataset', 'sample_id'],
                name='unique_sample_id_per_dataset',
            ),
        ]

    def __str__(self):
        return f'{self.dataset_id}/{self.sample_id}'

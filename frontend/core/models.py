from django.db import models

# Create your models here.
class PromoterModel(models.Model):
    organism_name = models.CharField(max_length=100)
    ncbi_id = models.CharField(max_length=50)
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    prediction_score = models.FloatField()
    sequence = models.CharField(max_length=200)
    annotation = models.CharField(max_length=3000)

    def __str__(self):
        return self.organism_name
    
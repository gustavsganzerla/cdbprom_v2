from django.db import models

# Create your models here.



class Organism(models.Model):
    assembly_annotation = models.CharField(max_length=100)
    kingdom = models.CharField(max_length=100)
    taxid = models.CharField(max_length=100)
    species_taxid = models.CharField(max_length=100)
    organism_name = models.CharField(max_length=100)
    infraspecific_name = models.CharField(max_length=100)
    asm_name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.assembly_annotation},{self.kingdom},{self.taxid},{self.organism_name}'
    

class PromoterModel(models.Model):
    organism_name = models.CharField(max_length=100)
    ncbi_id = models.CharField(max_length=50)
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    prediction_score = models.FloatField()
    sequence = models.CharField(max_length=200)
    annotation = models.CharField(max_length=3000)

    assembly_annotation = models.ForeignKey(Organism, on_delete=models.PROTECT,
                                            null=True,
                                            blank=True)

    def __str__(self):
        return self.organism_name
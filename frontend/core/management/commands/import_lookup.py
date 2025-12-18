from django.core.management.base import BaseCommand
from core.models import PromoterModel, Organism
from pathlib import Path
import os



class Command(BaseCommand):
    help = "Import data into the database"

    def add_arguments(self, parser):
        parser.add_argument('dirpath', type=str, help='Path to the directory with the files')

    def handle(self, *args, **kwargs):
        dirpath = Path(kwargs['dirpath'])

        if not dirpath.exists() or not dirpath.is_dir():
            self.stderr.write(self.style.ERROR(f"Invalid directory: {dirpath}"))
            return
        
        file = os.path.join(dirpath, 'bacteria_ready.csv')

        with open(file, 'r') as f:
            lines = f.readlines()

            for line in lines:
                aux = line.split(',')
                print(f'assembly_annotation: {aux[0]}')
                print(f'kingdom: {aux[1]}')
                print(f'taxid: {aux[2]}')
                print(f'species_taxid: {aux[3]}')
                print(f'organism_name: {aux[4]}')
                print(f'infraspecific_name: {aux[5]}')
                print(f'asm_name: {aux[6]}')

                obj = Organism(
                    assembly_annotation = aux[0],
                    kingdom = aux[1],
                    taxid = aux[2],
                    species_taxid = aux[3],
                    organism_name = aux[4],
                    infraspecific_name = aux[5],
                    asm_name = aux[6]
                )
                obj.save()




'''
assembly_annotation = models.CharField(max_length=100)
    kingdom = models.CharField(max_length=100)
    taxid = models.CharField(max_length=30)
    species_taxid = models.CharField(max_length=30)
    organism_name = models.CharField(max_length=100)
    infraspecific_name = models.CharField(max_length=30)
    asm_name = models.CharField(max_length=30)
'''
from django.core.management.base import BaseCommand
from core.models import PromoterModel, Organism
from pathlib import Path
import re

pattern = r"GCF_\d+\.\d+"

organism_cache = {o.assembly_annotation: o for o in Organism.objects.all()}


class Command(BaseCommand):
    help = "Import data into the database"

    def add_arguments(self, parser):
        parser.add_argument('dirpath', type=str, help='Path to the directory with the files')

    def handle(self, *args, **kwargs):
        dirpath = Path(kwargs['dirpath'])

        if not dirpath.exists() or not dirpath.is_dir():
            self.stderr.write(self.style.ERROR(f"Invalid directory: {dirpath}"))
            return
            
        files = list(dirpath.glob('*.txt'))


        for file in files:
            self.stdout.write(f"Importing {file.name}...")

            with file.open('r') as f:
                lines = f.readlines()

                if not lines:
                    self.stderr.write(self.style.warning(f"{file.name} is empty"))
                    continue

                for line in lines:
                    if 'Column' not in line:
                        values = line.strip().split('\t')
                        parts = file.name.split('_')
                        name = f"{parts[0]}_{parts[1]}" if len(parts) > 1 else parts[0]
                        match = re.search(pattern, file.name)
                        if match:
                            assembly_id = match.group()
                            organism_instance = organism_cache[assembly_id]
                        else:
                            assembly_id = "NA"

                        if len(values)>3:
                            print(f"organism_name: {name} ({len(name)})")
                            print(f"assembly id: {organism_instance}")
                            print(f"sequence: {values[8]} ({len(values[8])})")
                            print(f"annotation: {values[9]} ({len(values[9])})")
                            
                            obj = PromoterModel(
                                organism_name = name,
                                ncbi_id = values[0],
                                start_position = int(values[3]),
                                end_position = int(values[4]),
                                prediction_score = float(values[6]),
                                sequence = values[8],
                                annotation = values[9],
                                assembly_annotation = organism_instance
                            )
                            obj.save()
        self.stdout.write(self.style.SUCCESS("All files imported successfully"))

                            


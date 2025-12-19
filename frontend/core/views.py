from django.shortcuts import render
from . forms import QueryForm, InputForm
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PromoterModel, Organism
from .serializers import PromoterModelSerializer
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
import csv
from Bio import SeqIO
from io import StringIO
import logging
import requests
from urllib.parse import unquote_plus
import math

# Create your views here.

logger = logging.getLogger(__name__)

def home(request):
    all_data = PromoterModel.objects.values('organism_name')

    unique_organisms = len({d['organism_name'] for d in all_data})
    n_promoters = len(all_data)



    list_unique_kingdoms = []
    all_data_kingdoms = PromoterModel.objects.values('assembly_annotation__kingdom')
    for family in all_data_kingdoms:
        if family['assembly_annotation__kingdom'] not in list_unique_kingdoms:
            list_unique_kingdoms.append(family['assembly_annotation__kingdom'])



    
    return render(request, 'core/home.html', {'unique_organisms':unique_organisms,
                                              'n_promoters':n_promoters,
                                              'kingdoms':len(list_unique_kingdoms)})


def query(request):
    form = QueryForm()

    if request.method == 'POST':
        form = QueryForm(request.POST)

        if form.is_valid():
            gene = form.cleaned_data['gene_name']

    return render(request, 'core/query.html', {'form':form})


def resources(request):
    return render(request, 'core/resources.html')


def resources_api_db(request):
    return render(request, 'core/resources_api_db.html')

def contact(request):
    return render(request, 'core/contact.html')

def about(request):
    return render(request, 'core/about.html')

def organisms(request):
    organisms = (
        PromoterModel.objects
        .values('organism_name')      
        .annotate(count=Count('id'))   
        .order_by('organism_name')  
    )



    kingdoms = (
        PromoterModel.objects
        .values('assembly_annotation__kingdom')
        .annotate(unique_organisms=Count('assembly_annotation__organism_name', distinct=True))
    )

    


        

    return render(request, 'core/organisms.html', {'organisms': organisms,
                                                   'kingdoms':kingdoms})

def predict(request):
    output = []
    form = InputForm()
    return render(request, 'core/predict.html', {'form':form})




###this will be only for showing the results on screen, it uses pagination
class PromoterQueryView(APIView):
    def get(self, request):
        query = Q()

        organism_name = request.query_params.get('organism_name')
        annotation = request.query_params.get('annotation')
        ncbi_id = request.query_params.get('ncbi_id')

        ###here, i build the query to send to the DB API
        if organism_name:
            query &= Q(organism_name__icontains=organism_name)
        if annotation:
            annotation = unquote_plus(annotation)
            query &= Q(annotation__icontains=annotation)
        if ncbi_id:
            query &= Q(ncbi_id__icontains=ncbi_id)

        
        
        ###here, the sql query is prepared
        queryset = PromoterModel.objects.filter(query)

        ###here is when the query is executed
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)

        ###here the queryset is converted to a python dictionary
        serializer = PromoterModelSerializer(page, many=True)

        ###here, the data (ready) is sent to the frontend via http
        return paginator.get_paginated_response(serializer.data)


class PromoterDownloadCSVView(APIView):
    def get(self, request):
        query = Q()

        organism_name = request.query_params.get('organism_name')
        annotation = request.query_params.get('annotation')
        ncbi_id = request.query_params.get('ncbi_id')

        if organism_name:
            query &= Q(organism_name__icontains=organism_name)
        if annotation:
            query &= Q(annotation__icontains=annotation)
        if ncbi_id:
            query &= Q(ncbi_id__icontains=ncbi_id)

        results = PromoterModel.objects.filter(query).values(
            "ncbi_id", "organism_name", "sequence", "annotation"
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="promoters.csv"'

        writer = csv.writer(response)
        writer.writerow(['NCBI_ID', 'Organism_name', 'Promoter_sequence', 'Annotation'])

        for promoter in results:
            writer.writerow([
                promoter["ncbi_id"],
                promoter["organism_name"],
                promoter["sequence"],
                promoter["annotation"],
            ])

        return response
   

class DownloadPredictView(APIView):
    def post(self, request):
        data = request.data.get("data", [])

        if not data:
            return HttpResponse("No data received", status=400)
        
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="results_predictions.csv"'

        writer = csv.writer(response)

        if data:
            column_order = ["id", "Predicted class", "Probability promoter", "Probability non-promoter", "Coordinates", "Sequence", "Message"]
            writer.writerow(column_order)
        
        for row in data:
            writer.writerow([row.get(col, "") for col in column_order])
        
        return response


def autocomplete_organism_name(request):
    term = request.GET.get("q", "")

    results = []
    if term:
        queryset = (
            PromoterModel.objects.filter(organism_name__icontains=term)
            .values_list("organism_name", flat=True)
            .distinct()[:10]
        )
        results = list(queryset)

    return JsonResponse(results, safe=False)
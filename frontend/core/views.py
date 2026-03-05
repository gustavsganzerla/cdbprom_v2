from django.shortcuts import render
from . forms import QueryForm, InputForm, ContactForm
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

from django.core.mail import EmailMessage, get_connection
from django.conf import settings

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes

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

def resources_api_prediction(request):
    return render(request, 'core/resources_api_prediction.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            collected_data = form.cleaned_data
            subject = collected_data.get('subject')
            email = collected_data.get('email')
            message = collected_data.get('message')

            with get_connection(
                host = settings.EMAIL_HOST,
                port = settings.EMAIL_PORT,
                username = settings.EMAIL_HOST_USER,
                password = settings.EMAIL_HOST_PASSWORD,
                use_ssl = settings.EMAIL_USE_SSL
            ) as connection:
                subject = f'CDBProm_{subject}'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = ['eusebio.sganzerla@gmail.com']
                message = f'{message}\n{email}'

                email = EmailMessage(subject, message, email_from, recipient_list)
                email.send()

                return render(request, 'core/contact_success.html')




    
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form':form})

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
    print(kingdoms)

    


        

    return render(request, 'core/organisms.html', {'organisms': organisms,
                                                   'kingdoms':kingdoms})



def predict(request):
    output = []
    form = InputForm()
    return render(request, 'core/predict.html', {'form':form})


def docker(request):
    return render(request, 'core/docker.html')

###this will be only for showing the results on screen, it uses pagination
class PromoterQueryView(APIView):
    @extend_schema(
        summary="Search Organisms in PostgreSQL",
        description="Filters the database based on organism details, NCBI IDs, and protein families.",
        parameters=[
            OpenApiParameter(name='organism_name', description='Filter by name (e.g., E. coli)', required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name='annotation', description='Filter by genomic annotation', required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name='ncbi_id', description='Filter by NCBI Taxonomic ID', required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name='family', description='Filter by protein or organism family', required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name='organism_id', description='Filter by internal database ID', required=False, type=OpenApiTypes.INT),
        ],
        responses={200: PromoterModelSerializer(many=True)}, 
        tags=['Database Queries']
    )
    def get(self, request):
        query = Q()

        organism_name = request.query_params.get('organism_name')
        annotation = request.query_params.get('annotation')
        ncbi_id = request.query_params.get('ncbi_id')
        family = request.query_params.get('family')
        organism_id = request.query_params.get('organism_id')


        ###here, i build the query to send to the DB API
        if organism_name:
            organism_name = unquote_plus(organism_name)
            query &= Q(organism_name__icontains=organism_name)
        if annotation:
            annotation = unquote_plus(annotation)
            query &= Q(annotation__icontains=annotation)
        if ncbi_id:
            query &= Q(ncbi_id__icontains=ncbi_id)
        if organism_id:
            query &= Q(assembly_annotation_id=organism_id)
            
        
        if family and not organism_id:
            organisms =(
                Organism.objects
                .filter(kingdom=family)
                .annotate(sequence_count=Count("promotermodel"))
                .filter(sequence_count__gt=0)
                .order_by("organism_name")
                .values("id", "organism_name", "sequence_count")
            )

            return Response({
                "level":"family",
                "family":family,
                "results":list(organisms),
                "count":len(list(organisms))
            })

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
    @extend_schema(exclude=True)##this is to remove the API from swagger, it will get all APIViews as its exhaustive
    def get(self, request):
        query = Q()

        organism_name = request.query_params.get('organism_name')
        annotation = request.query_params.get('annotation')
        ncbi_id = request.query_params.get('ncbi_id')
        family = request.query_params.get('family')
        organism_id = request.query_params.get('organism_id')

        print(f"Query:{request.query_params}")

        # Build query
        if organism_name:
            organism_name = unquote_plus(organism_name)
            query &= Q(assembly_annotation__organism_name__icontains=organism_name)

        if annotation:
            annotation = unquote_plus(annotation)
            query &= Q(annotation__icontains=annotation)

        if ncbi_id:
            query &= Q(ncbi_id__icontains=ncbi_id)

        if organism_id:
            query &= Q(assembly_annotation_id=organism_id)


        # If no filters are provided, this will return all records
        results = PromoterModel.objects.filter(query).values(
            "ncbi_id", "organism_name", "sequence", "annotation"
        )


        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="promoters.csv"'

        writer = csv.writer(response)
        writer.writerow(["NCBI ID", "Organism Name", "Sequence", "Annotation"])

        for row in results:
            writer.writerow([
                row['ncbi_id'],
                row['organism_name'],
                row['sequence'],
                row['annotation']
            ])

        return response

   

class DownloadPredictView(APIView):
    @extend_schema(exclude=True)
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
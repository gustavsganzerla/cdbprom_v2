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

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter, OpenApiExample
from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes

from django.core.cache import cache
from django.core.paginator import Paginator

from rest_framework import status
import os
from dotenv import load_dotenv



load_dotenv()
# Create your views here.

logger = logging.getLogger(__name__)

def home(request):
    promoters = cache.get('promoters')
    kingdoms = cache.get('kingdoms')
    species = cache.get('species')
    
    if promoters is None:
        promoters = PromoterModel.objects.count()
        cache.set('promoters', promoters, 86400)

    if kingdoms is None:
        kingdoms = (PromoterModel.objects
            .values('assembly_annotation__kingdom')
            .distinct()
            .count()
        )
        cache.set('kingdoms', kingdoms, 86400)
    if species is None:
        species = (
            PromoterModel.objects
            .values('organism_name')
            .distinct()
            .count()
        )
        cache.set('species', species, 86400)

    return render(request, 'core/home.html', {"promoters": promoters, "kingdoms":kingdoms, "species":species})


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
    organisms = cache.get('organisms_list')
    kingdoms = cache.get('kingdoms_list')

    if organisms is None:
        organisms=list(
            PromoterModel.objects
            .values('organism_name')
            .annotate(count=Count('id'))   
            .order_by('organism_name')
        )
        cache.set('organisms_list', organisms, 86400)

    if kingdoms is None:
        kingdoms=list(
             PromoterModel.objects
            .values('assembly_annotation__kingdom')
            .annotate(unique_organisms=Count('assembly_annotation__organism_name', distinct=True))
        )
        cache.set('kingdoms_list', kingdoms, 86400)

    
    if kingdoms is None:
        kingdoms = []

    # -------- Pagination --------
    paginator = Paginator(kingdoms, 10)  # 10 rows per page
    page_number = request.GET.get("page", 1)

    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1

    # Ensure page_number is within valid range
    if page_number < 1:
        page_number = 1
    elif page_number > paginator.num_pages:
        page_number = paginator.num_pages if paginator.num_pages > 0 else 1

    kingdoms_page = paginator.get_page(page_number)

    return render(
        request,
        "core/organisms.html",
        {
            "organisms": organisms,
            "kingdoms": kingdoms_page
        }
    )



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

        ###build the paginator
        paginator = PageNumberPagination()
        paginator.page_size = 10
        

        #####FAMILY LEVEL
        if family and not organism_id:

            organisms = (
                Organism.objects
                .filter(kingdom=family)
                .annotate(sequence_count=Count("promotermodel"))
                .filter(sequence_count__gt=0)
                .order_by("organism_name")
                .values("id", "organism_name", "sequence_count")
            )

            page = paginator.paginate_queryset(organisms, request)

            response = paginator.get_paginated_response(page)

            # metadata for the JS to know it should render the organism table
            response.data["level"] = "family"
            response.data["family"] = family

            return response
        
        ######PROMOTER LEVEL
        queryset = PromoterModel.objects.filter(query)

        page = paginator.paginate_queryset(queryset, request)

        serializer = PromoterModelSerializer(page, many=True)

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


class SequencyProxyView(APIView):
    @extend_schema(
    summary="Send sequences for prediction",
    description="Sends sequences to the DNABERT framework. Each sequence must have an explicit 'id' and 'seq' field.",
    request=inline_serializer(
        name='SequenceRequest',
        fields={
            'sequences': serializers.ListField(
                child=inline_serializer(
                    name='SequenceItem',
                    fields={
                        'id': serializers.CharField(help_text="Sequence identifier"),
                        'seq': serializers.CharField(help_text="Nucleotide sequence (ATCG)")
                    }
                ),
                help_text="List of sequence objects"
            )
        }
    ),
    responses={200: serializers.DictField()},
    tags=['Prediction']
    )
    def post(self, request, *args, **kwargs):
        ####external flask API details
        flask_url = os.environ.get("PREDICTION_API_URL")
        api_key = os.environ.get("API_KEY")

        sequences = request.data.get('sequences')
        
        
        if not sequences:
            return Response({"error": "No sequences provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = requests.post(
                flask_url,
                json={"sequences":sequences},
                headers={"X-API-KEY":api_key},
                timeout=60
            )
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            return Response(
                {"error":f'API connection failed: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )


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
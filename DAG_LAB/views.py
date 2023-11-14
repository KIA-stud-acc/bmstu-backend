
import psycopg2
from DAG_LAB.models import *
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from DAG_LAB.serializers import *
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from minio import Minio
import logging
from django.conf import settings
from urllib.request import urlopen
from django.views.decorators.csrf import csrf_exempt
import datetime


fmt = getattr(settings, 'LOG_FORMAT', None)
lvl = getattr(settings, 'LOG_LEVEL', logging.DEBUG)

logging.basicConfig(format=fmt, level=lvl)
logging.debug("Logging started on %s for %s" % (logging.root.name, logging.getLevelName(lvl)))

client = Minio(endpoint="localhost:9000",   # адрес сервера
               access_key='ADMIN',          # логин админа
               secret_key='O5JZoWWq6tYE7XCTWJwGXEZGiUSAWU7e9yALGd2v',       # пароль админа
               secure=False)                # опциональный параметр, отвечающий за вкл/выкл защищенное TLS соединение

conn = psycopg2.connect(dbname="DAG", host="localhost", user="admin", password="admin", port="5432")
cursor = conn.cursor()
def get_creator():
    return 1
def get_admin():
    return 2

class NameOptionsList(APIView):
    model_class = NameOptions
    serializer_class = NameOptionsSerializer

    def get(self, request, format=None):
        sear = request.GET.get('text', "")
        NOList = self.model_class.objects.filter(status = "действует").filter(name__icontains=sear).order_by('name')
        serializer = self.serializer_class(NOList, many=True)
        return Response(serializer.data)
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NameOptionDetail(APIView):
    model_class = NameOptions
    serializer_class = NameOptionsSerializer
    def get(self, request, id, format=None):
        NameOption = self.model_class.objects.filter(id=id)[0]
        Result = Results.objects.filter(voting=id)
        serializer1 = self.serializer_class(NameOption)
        serializer2 = ResultsSerializer(Result, many=True)
        return Response({"voting": serializer1.data, "results": serializer2.data})
    def delete(self, request, id, format=None):
        if str(id) + "/" in [obj.object_name for obj in client.list_objects(bucket_name="images")]:
            for obj in [obj.object_name for obj in client.list_objects(bucket_name="images", prefix=str(id) + "/")]:
                client.remove_object(bucket_name="images", object_name=obj)
        NameOption = get_object_or_404(self.model_class, id=id)
        NameOption.status = "удалён"
        NameOption.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def post(self, request, id, format=None):
        src = request.data.get("src", 0)
        name = request.data.get("name", str(id))
        if src:
            if str(id)+"/" in [obj.object_name for obj in client.list_objects(bucket_name="images")]:
                for obj in [obj.object_name for obj in client.list_objects(bucket_name="images", prefix = str(id)+"/")]:
                    client.remove_object(bucket_name="images", object_name=obj)
            img = urlopen(src)
            img1 = urlopen(src)
            client.put_object(bucket_name='images',  # необходимо указать имя бакета,
                            object_name=str(id)+"/"+name+"."+src.split(".")[-1],  # имя для нового файла в хранилище
                            data=img,
                            length=len(img1.read())
                              )
            return Response(status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, id, format=None):
        """
        Обновляет информацию о голосовании (для модератора)
        """
        NameOption = get_object_or_404(self.model_class, id=id)
        serializer = self.serializer_class(NameOption, data=request.data.get('voting'), partial=True)
        if request.data.get('results', 0):
            Results.objects.filter(voting=id).delete()
            for obj in request.data.get('results'):
                obj["voting"] = id
                res_serializer = ResultsSerializer(data=obj)
                if res_serializer.is_valid():
                    res_serializer.save()
                else:
                    return Response(res_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            res_serializer = ResultsSerializer(Results.objects.filter(voting=id), many=True)
        if request.data.get('voting', 0):
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.serializer_class(NameOption)
        return Response({"voting": serializer.data, "results": res_serializer.data})
class VotingResList(APIView):
    model_class = VotingRes
    serializer_class = VotingResSerializer
    def get(self, request, format=None):
        status = request.GET.get('status', "")
        dateFrom = request.GET.get('dateFrom', "0001-01-01")
        dateTo = request.GET.get('dateTo', "9999-12-01")
        if status:
            NOList = self.model_class.objects.filter(status=status).filter(date_of_formation__date__gte=dateFrom).filter(date_of_formation__date__lte=dateTo).order_by('date_of_formation')
        else:
            NOList = self.model_class.objects.filter(date_of_formation__date__gte=dateFrom).filter(date_of_formation__date__lte=dateTo).order_by('date_of_formation')
        serializer = self.serializer_class(NOList, many=True)
        return Response(serializer.data)

class VotingResDetail(APIView):
    model_class = VotingRes
    serializer_class = VotingResSerializer
    def get(self, request, id, format=None):
        Appl = self.model_class.objects.filter(id=id)[0]
        ApplVot = Applserv.objects.filter(votingres=id)
        Voting = NameOptions.objects.filter(id__in=[obj['nameoption'] for obj in list(ApplVot.values("nameoption"))])
        serializer1 = self.serializer_class(Appl)
        serializer2 = NameOptionsSerializer(Voting, many=True)
        return Response({"Application": serializer1.data, "Voting": serializer2.data})

@api_view(['Put'])
def formAppl(request, id, format=None):
    Appl = get_object_or_404(VotingRes, id=id)
    if Appl.creator_id == get_creator() and Appl.status == "черновик":
        Appl.status = "сформирован"
        Appl.date_of_formation = datetime.datetime.now()
        Appl.save()
        ser = VotingResSerializer(Appl)
        return Response(ser.data)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
def delAppl(request, id, format=None):
    Appl = get_object_or_404(VotingRes, id=id)
    if Appl.creator_id == get_creator() and Appl.status == "черновик":
        Appl.status = "удалён"
        Appl.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
@api_view(['Put'])
def completeAppl(request, id, format=None):
    Appl = get_object_or_404(VotingRes, id=id)
    if list(Users.objects.filter(id=get_admin()).values())[0]['moderator'] is True and Appl.status == "сформирован":
        Appl.status = "завершён"
        Appl.moderator_id = get_admin()
        Appl.date_of_completion = datetime.datetime.now()
        Appl.save()
        ser = VotingResSerializer(Appl)
        return Response(ser.data)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
def cancelAppl(request, id, format=None):
    Appl = get_object_or_404(VotingRes, id=id)
    if list(Users.objects.filter(id=get_admin()).values())[0]['moderator'] is True and Appl.status == "сформирован":
        Appl.status = "отклонён"
        Appl.moderator_id = get_admin()
        Appl.date_of_completion = datetime.datetime.now()
        Appl.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
@api_view(['POST'])
def addToAppl(request, id, format=None):
    ApplId = request.data["id"]
    if ApplId:
        Appl = get_object_or_404(VotingRes, id=ApplId)
        if Appl.creator_id == get_creator() and Appl.status == "черновик":
            ser = ApplservSerializer(data={"votingRes":request.data["id"], "nameOption": id})
            if ser.is_valid():
                ser.save()
            return Response(ser.data)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    return Response(status=status.HTTP_400_BAD_REQUEST)
@api_view(['DELETE'])
def delFromAppl(request, id, format=None):
    ApplId = request.data["idAppl"]
    if ApplId:
        Appl = get_object_or_404(VotingRes, id=ApplId)
        if Appl.creator_id == get_creator() and Appl.status == "черновик":
            Applserv.objects.filter(nameOption = id).filter(votingRes=request.data["idAppl"]).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    return Response(status=status.HTTP_400_BAD_REQUEST)

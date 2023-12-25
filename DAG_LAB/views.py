
import psycopg2
from DAG_LAB.models import *
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from DAG_LAB.serializers import *
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from minio import Minio
import logging
from django.conf import settings
from urllib.request import urlopen
import datetime
from django.core.validators import URLValidator
from pathlib import Path
import socket
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from DAG_LAB.permissions import IsManager
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
import redis
import uuid

fmt = getattr(settings, 'LOG_FORMAT', None)
lvl = getattr(settings, 'LOG_LEVEL', logging.DEBUG)

logging.basicConfig(format=fmt, level=lvl)
logging.debug("Logging started on %s for %s" % (logging.root.name, logging.getLevelName(lvl)))

client = Minio(endpoint="localhost:9000",   # адрес сервера
               access_key='ADMIN',          # логин админа
               secret_key='O5JZoWWq6tYE7XCTWJwGXEZGiUSAWU7e9yALGd2v',       # пароль админа
               secure=False)                # опциональный параметр, отвечающий за вкл/выкл защищенное TLS соединение

session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT)


conn = psycopg2.connect(dbname="DAG", host="localhost", user="admin", password="admin", port="5432")
cursor = conn.cursor()

def check_session(request):
    ssid = request.COOKIES.get("session_id", -1)
    username = session_storage.get(ssid)
    if not username:
        return -1
    else:
        return get_object_or_404(User, username=username.decode('utf-8'))

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator



class NameOptionsList(APIView):
    model_class = NameOptions
    serializer_class = NameOptionsSerializer
    def get(self, request, format=None):
        ssid = request.COOKIES.get("session_id", -1)
        username = session_storage.get(ssid)
        if not username:
            sear = request.GET.get('text', "")
            NOList = self.model_class.objects.filter(status="действует").filter(name__icontains=sear).order_by('name')
            serializer = self.serializer_class(NOList, many=True)
            for i in serializer.data:
                i["image_src"] = i["image_src"].replace("127.0.0.1",
                                                        "192.168.31.235")  # socket.gethostbyname(socket.gethostname()))
                i["image_src"] = i["image_src"].replace("localhost",
                                                        "192.168.31.235")  # socket.gethostbyname(socket.gethostname()))
            return Response({"voting": serializer.data})
        else:
            user = get_object_or_404(User, username=username.decode('utf-8'))
        try:
            Appl = get_object_or_404(VotingRes, creator=user.id, status="черновик").id
        except:
            Appl = None
        sear = request.GET.get('text', "")
        NOList = self.model_class.objects.filter(status = "действует").filter(name__icontains=sear).order_by('name')
        serializer = self.serializer_class(NOList, many=True)
        for i in serializer.data:
            i["image_src"] = i["image_src"].replace("127.0.0.1", "192.168.31.235")   #socket.gethostbyname(socket.gethostname()))
            i["image_src"] = i["image_src"].replace("localhost", "192.168.31.235")   #socket.gethostbyname(socket.gethostname()))
        return Response({"voting":serializer.data, "draftID": Appl})

    @method_permission_classes((IsManager,))
    @swagger_auto_schema(request_body=NameOptionsSerializer)
    @csrf_exempt
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
        serializer1 = self.serializer_class(NameOption)
        i = serializer1.data
        i["image_src"] = i["image_src"].replace("127.0.0.1", "192.168.31.235")   #socket.gethostbyname(socket.gethostname()))
        i["image_src"] = i["image_src"].replace("localhost", "192.168.31.235")   #socket.gethostbyname(socket.gethostname()))
        return Response(i)

    @csrf_exempt
    @method_permission_classes((IsManager,))
    def delete(self, request, id, format=None):
        if str(id) + "/" in [obj.object_name for obj in client.list_objects(bucket_name="images")]:
            for obj in [obj.object_name for obj in client.list_objects(bucket_name="images", prefix=str(id) + "/")]:
                client.remove_object(bucket_name="images", object_name=obj)
        NameOption = get_object_or_404(self.model_class, id=id)
        NameOption.image_src = None
        NameOption.status = "удалён"
        NameOption.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @csrf_exempt
    @method_permission_classes((IsManager,))
    def post(self, request, id, format=None):
        src = request.data.get("src", 0)
        name = request.data.get("name", str(id))
        NameOption = get_object_or_404(self.model_class, id=id)
        file = request.FILES['image']
        if src and NameOption:
            if str(id)+"/" in [obj.object_name for obj in client.list_objects(bucket_name="images")]:
                for obj in [obj.object_name for obj in client.list_objects(bucket_name="images", prefix = str(id)+"/")]:
                    client.remove_object(bucket_name="images", object_name=obj)
            val = URLValidator()

            val(src)
            img = urlopen(src)
            img1 = urlopen(src)
            client.put_object(bucket_name='images',  # необходимо указать имя бакета,
                              object_name=str(id) + "/" + name + "." + src.split(".")[-1],
                              # имя для нового файла в хранилище
                              data=img,
                              length=len(img1.read())
                              )
            NameOption.image_src = f"http://localhost:9000/images/{id}/{name}.{src.split('.')[-1]}"
            NameOption.save()
            return Response(status=status.HTTP_201_CREATED)
        elif file and NameOption:
            if str(id) + "/" in [obj.object_name for obj in client.list_objects(bucket_name="images")]:
                for obj in [obj.object_name for obj in client.list_objects(bucket_name="images", prefix=str(id) + "/")]:
                    client.remove_object(bucket_name="images", object_name=obj)
            client.put_object(bucket_name='images',  # необходимо указать имя бакета,
                              object_name=str(id) + "/" + name + Path(file.name).suffix,
                              # имя для нового файла в хранилище
                              data=file,
                              length=len(file)
                              )

            NameOption.image_src = f"http://localhost:9000/images/{id}/{name}{Path(file.name).suffix}"
            NameOption.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @csrf_exempt
    @method_permission_classes((IsManager,))
    @swagger_auto_schema(request_body=NameOptionsSerializer)
    def put(self, request, id, format=None):
        """
        Обновляет информацию о голосовании (для модератора)
        """
        NameOption = get_object_or_404(self.model_class, id=id)
        serializer = self.serializer_class(NameOption, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)
class VotingResList(APIView):
    model_class = VotingRes
    serializer_class = VotingResSerializer
    authentication_classes = [BasicAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        user = check_session(request)
        if user == -1:
            return Response(status=status.HTTP_403_FORBIDDEN)
        stat = request.GET.get('status', "")
        dateFrom = request.GET.get('dateFrom', "0001-01-01")
        dateTo = request.GET.get('dateTo', "9999-12-01")
        if user.is_staff:
            if stat:
                NOList = self.model_class.objects.filter(status=stat).filter(date_of_formation__date__gte=dateFrom).filter(date_of_formation__date__lte=dateTo).order_by('date_of_formation')
            else:
                NOList = self.model_class.objects.filter(date_of_formation__date__gte=dateFrom).filter(date_of_formation__date__lte=dateTo).order_by('date_of_formation')
            serializer = self.serializer_class(NOList, many=True)
            for i in serializer.data:
                if i["creator"]:
                    i["creator"] = list(User.objects.values("id","username","email","phone").filter(id=i["creator"]))[0]
                if i["moderator"]:
                    i["moderator"] = list(User.objects.values("id", "username", "email", "phone").filter(id=i["moderator"]))[0]
        else:
            if stat:
                NOList = self.model_class.objects.filter(status=stat).filter(date_of_formation__date__gte=dateFrom).filter(date_of_formation__date__lte=dateTo).filter(creator=user.id).order_by('date_of_formation')
            else:
                NOList = self.model_class.objects.filter(date_of_formation__date__gte=dateFrom).filter(date_of_formation__date__lte=dateTo).filter(creator=user.id).order_by('date_of_formation')
            serializer = self.serializer_class(NOList, many=True)
            for i in serializer.data:
                if i["creator"]:
                    i["creator"] = list(User.objects.values("id","username","email","phone").filter(id=i["creator"]))[0]
                if i["moderator"]:
                    i["moderator"] = list(User.objects.values("id", "username", "email", "phone").filter(id=i["moderator"]))[0]
        return Response(serializer.data)

class VotingResDetail(APIView):
    model_class = VotingRes
    serializer_class = VotingResSerializer
    permission_classes = [IsAuthenticated]
    def get(self, request, id, format=None):
        user = check_session(request)
        if user == -1:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if id == 0:
            try:
                Appl = self.model_class.objects.filter(status="черновик").filter(creator=user.id)[0]
            except IndexError:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if user.is_staff:
                try:
                    Appl = self.model_class.objects.filter(id=id)[0]
                except IndexError:
                    return Response(status=status.HTTP_404_NOT_FOUND)
            else:
                try:
                    Appl = self.model_class.objects.filter(id=id).filter(creator=user.id)[0]
                except IndexError:
                    return Response(status=status.HTTP_404_NOT_FOUND)

        ApplVot = Applserv.objects.filter(votingRes=id)
        Voting = NameOptions.objects.filter(id__in=[obj['nameOption'] for obj in list(ApplVot.values("nameOption"))])
        serializer1 = self.serializer_class(Appl)
        serializer2 = NameOptionsSerializer(Voting, many=True)
        res = {"Application": serializer1.data, "Voting": serializer2.data}
        for vote in res["Voting"]:
            vote["percentage"] = get_object_or_404(Applserv, nameOption=vote["id"], votingRes=id).percentageofvotes
        if res["Application"]["creator"]:
            res["Application"]["creator"] = \
            list(User.objects.values("id", "username", "email", "phone").filter(id=res["Application"]["creator"]))[0]
        if res["Application"]["moderator"]:
            res["Application"]["moderator"] = \
            list(User.objects.values("id", "username", "email", "phone").filter(id=res["Application"]["moderator"]))[0]
        return Response(res)

    @csrf_exempt
    def put(self, request, id, format=None):
        user = check_session(request)
        if user == -1:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            Appl = get_object_or_404(VotingRes, id=id, creator=user.id)
        except:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        desc = request.data.get("description", 0)
        if desc and Appl:
            logging.debug(desc)
            Appl.description = desc
            Appl.save()
            ser = VotingResSerializer(Appl)
            return Response(ser.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['Put'])
def formAppl(request, format=None):
    user = check_session(request)
    if user == -1:
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        Appl = get_object_or_404(VotingRes, creator=user.id, status="черновик")
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    Appl.status = "сформирован"
    Appl.date_of_formation = datetime.datetime.now()
    Appl.save()
    ser = VotingResSerializer(Appl)
    return Response(ser.data)

@csrf_exempt
@api_view(['DELETE'])
def delAppl(request, format=None):
    user = check_session(request)
    if user == -1:
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        Appl = get_object_or_404(VotingRes, creator=user.id, status="черновик")
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    Appl.status = "удалён"
    Appl.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


@csrf_exempt
@swagger_auto_schema(method='Put', request_body=VotingResSerializer)
@api_view(['Put'])
@permission_classes((IsManager,))
def chstatusAppl(request, id, format=None):
    user = check_session(request)
    if user == -1:
        return Response(status=status.HTTP_403_FORBIDDEN)
    #if user.is_staff == False:
    #    return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        Appl = get_object_or_404(VotingRes, id=id)
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    stat = request.data.get('status', 0)
    if Appl.status == "сформирован" and stat in ["отклонён", "завершён"]:  #list(Users.objects.filter(id=get_admin()).values())[0]['is_staff'] is True and
        Appl.status = stat
        Appl.moderator_id = user.id
        Appl.date_of_completion = datetime.datetime.now()
        Appl.save()
        ser = VotingResSerializer(Appl)
        return Response(ser.data)
    return Response(status=status.HTTP_403_FORBIDDEN)

@csrf_exempt
@api_view(['POST'])
def addToAppl(request, id, format=None):
    user = check_session(request)
    if user == -1:
        return Response(status=status.HTTP_403_FORBIDDEN)

    percent = request.data.get("percent", 0)
    try:
        Appl = get_object_or_404(VotingRes, creator=user.id, status="черновик")
        logging.debug(Appl)
    except:
        serializer = VotingResSerializer(data={"creator": user.id})
        if serializer.is_valid():
            serializer.save()
        Appl = get_object_or_404(VotingRes, creator=user.id, status="черновик")
        logging.debug(Appl)
    ser = ApplservSerializer(data={"votingRes":Appl.id, "nameOption": id, "percentageofvotes": float(percent)})
    if ser.is_valid():
        logging.debug(ser.validated_data)
        ser.save()
    else:
        logging.debug(ser.is_valid())
    return Response(ser.data)


class MM(APIView):

    @csrf_exempt
    def delete(self, request, idAppl, idServ, format=None):
        user = check_session(request)
        if user == -1:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            get_object_or_404(VotingResSerializer, id=idAppl, creator=user.id)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            applserv = get_object_or_404(Applserv, nameOption=idServ, votingRes=idAppl)
            applserv.delete()
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @csrf_exempt
    def put(self, request, idAppl, idServ, format=None):
        user = check_session(request)
        if user == -1:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            get_object_or_404(VotingResSerializer, id=idAppl, creator=user.id)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            applserv = get_object_or_404(Applserv, nameOption=idServ, votingRes=idAppl)
        except:
           return Response(status=status.HTTP_404_NOT_FOUND)
        percent = request.data.get("percent", 0)
        if percent:
            applserv.percentageofvotes = percent
            applserv.save()
            ser = ApplservSerializer(applserv)
            return Response(ser.data)
        Response(status=status.HTTP_400_BAD_REQUEST)



class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    queryset = User.objects.all()
    serializer_class = UsersSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.object = serializer.save()
            self.object.set_password(self.object.password)
            self.object.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsManager]
        return [permission() for permission in permission_classes]


@csrf_exempt
@swagger_auto_schema(method='post', request_body=UsersSerializer)
@authentication_classes([])
@api_view(['Post'])
def login_view(request):
    username = request.data.get("username") # допустим передали username и password
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        random_key = uuid.uuid4()
        session_storage.set(str(random_key), username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

@api_view(('GET',))
def logout_view(request):
    ssid = request.COOKIES.get("session_id", -1)
    session_storage.delete(ssid)
    logout(request)
    return Response({'status': 'Success'})


@csrf_exempt
@api_view(['Put'])
def putQuantityOfVotes(request):
    if request.data.get('Key',-1) != 123456:
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        Appl = get_object_or_404(VotingRes, id=request.data.get('Id',-1))
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    Appl.QuantityOfVotes = request.data.get("QuantityOfVotes", 0)
    Appl.save()
    return Response({'status': 'Success'})


@api_view(('GET',))
def userInfo(request):
    user = check_session(request)
    if user == -1:
        return Response(status=status.HTTP_403_FORBIDDEN)
    return Response(UsersSerializer(user).data)

#<Response status_code=403, "text/html; charset=utf-8">
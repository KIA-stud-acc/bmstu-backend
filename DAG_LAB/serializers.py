from DAG_LAB.models import *
from rest_framework import serializers


class NameOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = NameOptions
        # Поля, которые мы сериализуем
        fields = ["id", "name", "type", "status", "image_src"]


class VotingResSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingRes
        fields = ["id", "status", "creator", "moderator", "date_of_creation", "date_of_formation", "date_of_completion", "description"]

class ApplservSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applserv
        fields = ["nameOption", "votingRes", "percentageofvotes"]

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["id", "name", "mail", "phone", "password", "moderator"]
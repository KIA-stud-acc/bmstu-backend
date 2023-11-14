from DAG_LAB.models import *
from rest_framework import serializers


class NameOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = NameOptions
        # Поля, которые мы сериализуем
        fields = ["id", "name", "description", "status"]

class ResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Results
        fields = ["id", "case", "votes", "voting"]

class VotingResSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingRes
        fields = ["id", "status", "creator", "moderator", "date_of_creation", "date_of_formation", "date_of_completion"]

class ApplservSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applserv
        fields = ["nameOption", "votingRes"]
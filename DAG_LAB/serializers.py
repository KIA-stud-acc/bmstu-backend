from DAG_LAB.models import *
from rest_framework import serializers
from collections import OrderedDict


class NameOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = NameOptions
        # Поля, которые мы сериализуем
        fields = ["id", "name", "type", "status", "image_src"]

        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields


class VotingResSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingRes
        fields = ["id", "status", "creator", "moderator", "date_of_creation", "date_of_formation", "date_of_completion", "description", "QuantityOfVotes"]

        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields

class ApplservSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applserv
        fields = ["nameOption", "votingRes", "percentageofvotes"]

        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields

class UsersSerializer(serializers.ModelSerializer):
    #is_staff = serializers.BooleanField(default=False, required=False)
    #is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "password"]  # , "is_staff", "is_superuser"

        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields
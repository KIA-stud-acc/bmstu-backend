from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.db import models
import logging
from django.conf import settings

fmt = getattr(settings, 'LOG_FORMAT', None)
lvl = getattr(settings, 'LOG_LEVEL', logging.DEBUG)

logging.basicConfig(format=fmt, level=lvl)
logging.debug("Logging started on %s for %s" % (logging.root.name, logging.getLevelName(lvl)))



# Create your models here.
class Applserv(models.Model):
    nameOption = models.ForeignKey('NameOptions', models.DO_NOTHING, db_column='nameOption')  # Field name made lowercase. The composite primary key (nameOption, votingRes) found, that is not supported. The first column is selected.
    votingRes = models.ForeignKey('VotingRes', models.DO_NOTHING, db_column='votingRes')  # Field name made lowercase.
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    percentageofvotes = models.FloatField(db_column='PercentageOfVotes', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'applServ'
        unique_together = (('nameOption', 'votingRes'),)


class NameOptions(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.TextField()
    type = models.TextField(blank=True, null=True)
    status = models.TextField(default="действует")
    image_src = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'name options'



class User(AbstractBaseUser, PermissionsMixin): # Field name made lowercase.
    id = models.AutoField(primary_key=True)
    username = models.TextField(db_column='name', unique=True)
    email = models.EmailField(("email адрес"), blank=True, null=True, unique=True)
    phone = models.TextField(blank=True, null=True, unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    USERNAME_FIELD = 'username'
    objects = UserManager()
    class Meta:
        db_table = 'User'


class VotingRes(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    status = models.TextField(default="черновик", blank=True, null=True)
    creator = models.ForeignKey(User, models.DO_NOTHING, db_column='creator', blank=True)
    moderator = models.ForeignKey(User, models.DO_NOTHING, db_column='moderator', related_name='votingres_moderator_set', blank=True, null=True)
    date_of_creation = models.DateTimeField(auto_now=True, db_column='date of creation', blank=True)  # Field renamed to remove unsuitable characters.
    date_of_formation = models.DateTimeField(db_column='date of formation', blank=True, null=True)  # Field renamed to remove unsuitable characters.
    date_of_completion = models.DateTimeField(db_column='date of completion', blank=True, null=True)  # Field renamed to remove unsuitable characters.
    description = models.TextField(blank=True, null=True)
    QuantityOfVotes = models.IntegerField(db_column='QuantityOfVotes', null=True)


    class Meta:
        managed = False
        db_table = 'voting res'

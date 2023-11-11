from django.db import models

# Create your models here.
class Applserv(models.Model):
    nameoption = models.OneToOneField('NameOptions', models.DO_NOTHING, db_column='nameOption', primary_key=True)  # Field name made lowercase. The composite primary key (nameOption, votingRes) found, that is not supported. The first column is selected.
    votingres = models.ForeignKey('VotingRes', models.DO_NOTHING, db_column='votingRes')  # Field name made lowercase.

    class Meta:
        db_table = 'applServ'
        unique_together = (('nameoption', 'votingres'),)


class NameOptions(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.TextField()
    src = models.TextField()
    description = models.TextField(blank=True, null=True)
    status = models.TextField()

    class Meta:
        db_table = 'name options'


class Results(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    case = models.TextField(blank=True, null=True)
    votes = models.BigIntegerField()
    voting = models.ForeignKey(NameOptions, models.DO_NOTHING, db_column='voting')

    class Meta:
        db_table = 'results'


class Users(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.TextField(unique=True)
    mail = models.TextField()
    phone = models.TextField(blank=True, null=True)
    password = models.TextField()
    moderator = models.BooleanField()

    class Meta:
        db_table = 'users'


class VotingRes(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    status = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(Users, models.DO_NOTHING, db_column='creator', blank=True, null=True)
    moderator = models.ForeignKey(Users, models.DO_NOTHING, db_column='moderator', related_name='votingres_moderator_set', blank=True, null=True)
    date_of_creation = models.DateTimeField(db_column='date of creation', blank=True, null=True)  # Field renamed to remove unsuitable characters.
    date_of_formation = models.DateTimeField(db_column='date of formation', blank=True, null=True)  # Field renamed to remove unsuitable characters.
    date_of_completion = models.DateTimeField(db_column='date of completion', blank=True, null=True)  # Field renamed to remove unsuitable characters.


    class Meta:
            db_table = 'voting res'

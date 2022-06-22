from django.db import models


class Task(models.Model):
    user = models.CharField(max_length=32)
    result = models.CharField(max_length=100)
    processing_time = models.IntegerField()
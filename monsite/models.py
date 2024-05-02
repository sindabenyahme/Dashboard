from django.db import models

class File(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='files/')

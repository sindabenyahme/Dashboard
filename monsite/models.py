from django.db import models

class File(models.Model):
    start_date = models.CharField(max_length=50)
    end_date = models.CharField(max_length=50)
    file = models.FileField(upload_to='files/')

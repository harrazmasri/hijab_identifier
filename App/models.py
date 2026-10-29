from django.db import models

# Create your models here.
class ImageMedia (models.Model):
    filename = models.CharField(max_length=100)
    extension = models.CharField(max_length=4)

    file = models.ImageField(
        upload_to='images/',
        blank=True,
        null=True,
    )

    def __str__ (self):
        return self.name

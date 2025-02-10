from django.db import models

from purse.ext.django.repo import PurseDjangoModel


class User(PurseDjangoModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"id={self.id}, name={self.name}"

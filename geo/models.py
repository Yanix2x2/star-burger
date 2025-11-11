from django.db import models
from django.utils import timezone

class AddressPoint(models.Model):
    address = models.CharField(
        'адрес', 
        max_length=500, 
        db_index=True,
        unique=True
    )
    latitude = models.DecimalField(
        'широта',
        max_digits=9, 
        decimal_places=6, 
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        'долгота',
        max_digits=9, 
        decimal_places=6, 
        null=True,
        blank=True
    )
    registered_at = models.DateTimeField(
        'дата и время регистрации',
        default=timezone.now
    )
    
    def __str__(self):
        return self.address

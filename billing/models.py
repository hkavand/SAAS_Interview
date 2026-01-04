from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    SUBSCRIPTION_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('none', 'None')
    ]
    
    subscription_status = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_CHOICES,
        default='inactive'
    )
    current_plan = models.CharField(
        max_length=10,
        choices=[
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('none', 'None')
    ],
        default='none'
    )

    # Lifetime value in cents
    total_amount_paid = models.BigIntegerField(default=0)

    def __str__(self):
        return self.username

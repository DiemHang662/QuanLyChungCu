from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
# Create your models here.

class Resident(AbstractUser):
    avatar = CloudinaryField(null=True)

    def __str__(self):
        return self.username

class Flat(models.Model):
    number = models.CharField(max_length=10)
    floor = models.IntegerField()

    def __str__(self):
        return self.number

class Bill(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField()
    due_date = models.DateField()
    bill_type = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=10, default='UNPAID')

    def __str__(self):
        return self.bill_type

class Item(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    status_choices = [
        ('PENDING', 'Pending'),
        ('RECEIVED', 'Received'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='PENDING')

    def __str__(self):
        return self.name
class Feedback(models.Model):
    title = models.CharField(max_length=70, default='Mất điện')
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Survey(models.Model):
    title = models.CharField(max_length=100)
    creator = models.ForeignKey(Resident, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class SurveyResult(models.Model):
    survey = models.ForeignKey('Survey', related_name='results', on_delete=models.CASCADE)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    cleanliness_rating = models.PositiveIntegerField()
    facilities_rating = models.PositiveIntegerField()
    services_rating = models.PositiveIntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.survey.title

class FaMember(models.Model):
    name = models.CharField(max_length=100)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    numberXe = models.CharField(max_length=8)

    def __str__(self):
        return self.name
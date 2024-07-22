from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
class Resident(AbstractUser):
    avatar = CloudinaryField('avatar',null=True)
    phone = models.CharField(max_length= 13, null = True, blank = True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.username

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField()
    image = CloudinaryField('image', null=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    resident = models.OneToOneField(Resident, on_delete=models.CASCADE)

class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cart.resident.username}'s Cart - {self.product.name}"

class Bill(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    issue_date = models.DateField()
    due_date = models.DateField()
    bill_type = models.CharField(max_length=50)
    status_choices = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
    ]
    payment_status = models.CharField(max_length=10, choices=status_choices, default='UNPAID')
    image = CloudinaryField('image', null=True)

    def __str__(self):
        return self.bill_type

class BillProduct(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='bill_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return self.product.name

class Flat(models.Model):
    number = models.CharField(max_length=10)
    floor = models.IntegerField()

    def __str__(self):
        return self.number

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

class FaMember(models.Model):
    name = models.CharField(max_length=100)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    numberXe = models.CharField(max_length=8)

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


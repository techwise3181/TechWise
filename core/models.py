from django.db import models
from django.contrib.auth.models import User

class ServiceRequest(models.Model):
    PROBLEM_TYPES = [
        ('Hardware', 'Hardware'),
        ('Software', 'Software'),
        ('Battery', 'Battery'),
        ('Screen', 'Screen'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests', null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20)
    laptop_model = models.CharField(max_length=100, blank=True, null=True)
    problem_type = models.CharField(max_length=20, choices=PROBLEM_TYPES)
    problem_description = models.TextField()
    photos = models.JSONField(default=list, blank=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default="Cash on Delivery")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.laptop_model or 'Unknown Model'}"

class LaptopSale(models.Model):
    STATUS_CHOICES = [
        ('Order Placed', 'Order Placed'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Packed', 'Packed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='laptop_sales', null=True, blank=True)
    laptop_name = models.CharField(max_length=200)
    laptop_specs = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default="Cash on Delivery")
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Order Placed')
    current_lat = models.FloatField(blank=True, null=True)
    current_lng = models.FloatField(blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale: {self.laptop_name} to {self.customer_name}"

    @property
    def price_total(self):
        return self.price * self.quantity

class LaptopRental(models.Model):
    STATUS_CHOICES = [
        ('Order Placed', 'Order Placed'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Packed', 'Packed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='laptop_rentals', null=True, blank=True)
    laptop_name = models.CharField(max_length=200)
    laptop_specs = models.TextField(blank=True, null=True)
    rental_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration = models.CharField(max_length=50) # e.g., "1 month"
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default="Cash on Delivery")
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Order Placed')
    current_lat = models.FloatField(blank=True, null=True)
    current_lng = models.FloatField(blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    rental_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rental: {self.laptop_name} for {self.customer_name}"

    @property
    def rental_total(self):
        return self.rental_price * self.quantity

class Laptop(models.Model):
    AVAILABILITY_CHOICES = [
        ('Sale', 'Sale Only'),
        ('Rent', 'Rent Only'),
        ('Both', 'Both Sale & Rent'),
    ]
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    specs = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(max_length=500)
    availability_type = models.CharField(max_length=10, choices=AVAILABILITY_CHOICES, default='Both')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.name}"

class CartItem(models.Model):
    TRANSACTION_CHOICES = [
        ('sale', 'Buy'),
        ('rental', 'Rent'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES, default='sale')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart: {self.laptop.name}"

    @property
    def total_price(self):
        if self.transaction_type == 'sale':
            return self.laptop.price * self.quantity
        return self.laptop.rent_price * self.quantity

class OTPVerification(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"OTP for {self.email}"

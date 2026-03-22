from django.contrib import admin
from .models import ServiceRequest, LaptopSale, LaptopRental, Laptop

admin.site.site_header = "TechWise Solutions Admin"
admin.site.site_title = "TechWise Admin Portal"
admin.site.index_title = "Welcome to TechWise Management"

@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'price', 'rent_price', 'availability_type', 'created_at')
    list_filter = ('brand', 'availability_type', 'created_at')
    search_fields = ('name', 'brand', 'specs')
    list_editable = ('price', 'rent_price', 'availability_type')
    list_per_page = 20

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'laptop_model', 'problem_type', 'state', 'district', 'payment_method', 'created_at')
    list_filter = ('problem_type', 'payment_method', 'state', 'created_at')
    search_fields = ('customer_name', 'email', 'laptop_model', 'problem_description', 'address', 'pincode', 'state', 'district')
    readonly_fields = ('created_at',)
    list_per_page = 20

@admin.register(LaptopSale)
class LaptopSaleAdmin(admin.ModelAdmin):
    list_display = ('laptop_name', 'customer_name', 'total_amount', 'state', 'district', 'payment_method', 'sale_date')
    list_filter = ('payment_method', 'state', 'sale_date')
    search_fields = ('laptop_name', 'customer_name', 'email', 'laptop_specs', 'address', 'pincode', 'state', 'district')
    readonly_fields = ('sale_date',)
    list_per_page = 20

@admin.register(LaptopRental)
class LaptopRentalAdmin(admin.ModelAdmin):
    list_display = ('laptop_name', 'customer_name', 'duration', 'total_amount', 'state', 'district', 'rental_date')
    list_filter = ('duration', 'state', 'rental_date')
    search_fields = ('laptop_name', 'customer_name', 'email', 'laptop_specs', 'address', 'pincode', 'state', 'district')
    readonly_fields = ('rental_date',)
    list_per_page = 20

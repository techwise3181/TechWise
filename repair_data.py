
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techwise_project.settings')
django.setup()

from core.models import LaptopSale, LaptopRental

SPECS_MAP = {
    'ASUS ROG Strix G16': 'Intel i9, RTX 4070, 32GB RAM, 1TB SSD',
    'Dell XPS 15': 'Intel i7, OLED Display, 16GB RAM, 512GB SSD',
    'HP Pavilion Gaming': 'Ryzen 7, GTX 1650, 16GB RAM, 512GB SSD',
    'Lenovo Legion 5': 'Ryzen 9, RTX 3060, 16GB RAM, 1TB SSD',
    'MacBook Air M2': 'M2 Chip, 8GB RAM, 256GB SSD, Liquid Retina',
    'Acer Nitro 5': 'Intel i5, RTX 3050, 8GB RAM, 512GB SSD'
}

def repair():
    updated = 0
    for sale in LaptopSale.objects.all():
        if not sale.laptop_specs:
            sale.laptop_specs = SPECS_MAP.get(sale.laptop_name, '')
            sale.save()
            updated += 1
            
    for rental in LaptopRental.objects.all():
        if not rental.laptop_specs:
            rental.laptop_specs = SPECS_MAP.get(rental.laptop_name, '')
            rental.save()
            updated += 1
            
    print(f"Successfully updated {updated} existing records.")

if __name__ == '__main__':
    repair()

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techwise_project.settings')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
email = 'admin@techwise.com'
password = 'adminpassword'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser created successfully!")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("You can now login at http://127.0.0.1:8000/admin")
else:
    print(f"User '{username}' already exists.")

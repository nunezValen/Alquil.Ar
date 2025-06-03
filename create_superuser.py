import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.utils import IntegrityError

def create_superuser():
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    
    try:
        user = User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully!")
        print(f"You can now log in to the admin interface at http://127.0.0.1:8000/admin with these credentials.")
    except IntegrityError:
        print(f"Error: A user with that username or email already exists.")
        choice = input("Do you want to try again? (y/n): ")
        if choice.lower() == 'y':
            create_superuser()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Create a new superuser for Django Admin")
    print("=======================================")
    create_superuser()
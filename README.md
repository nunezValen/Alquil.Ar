# Alquil.Ar

## Installation

To install the required dependencies for this project, follow these steps:

1. Make sure you have Python installed (Python 3.10 or higher is recommended).

2. Install the required packages using pip:

```bash
python -m pip install -r requirements.txt
```

This will install all the necessary dependencies, including:
- Django
- Pillow (required for image handling)
- django-widget-tweaks

## Accessing the Admin Interface

The Django admin interface is available at http://127.0.0.1:8000/admin when the server is running.

### Default Admin Accounts

The project comes with two default admin accounts:

1. Username: emp_mario@alquilar.com
   Password: MarioBro123!

2. Username: emp_luigi@alquilar.com
   Password: LuigiBro123!

### Creating a New Admin Account

If you're unable to log in with the default accounts, you can create a new superuser account using one of these methods:

#### Using the provided script:

```bash
python create_superuser.py
```

#### For Windows users, you can simply double-click on:

```
create_admin.bat
```

Follow the prompts to enter a username, email, and password for your new admin account.

#### Using Django's built-in command:

```bash
python manage.py createsuperuser
```

## Troubleshooting

### ImageField Error

If you encounter the following error:

```
ERRORS:
maquinas.MaquinaBase.imagen: (fields.E210) Cannot use ImageField because Pillow is not installed.
HINT: Get Pillow at https://pypi.org/project/Pillow/ or run command "python -m pip install Pillow".
```

This means that the Pillow library, which is required for Django's ImageField, is not installed. You can resolve this by running:

```bash
python -m pip install Pillow
```

Or by installing all dependencies using the requirements.txt file as mentioned above.

Alternatively, you can run the provided script:

```bash
python install_pillow.py
```

## Running the Project

After installing the dependencies, you can run the project with:

```bash
python manage.py runserver
```

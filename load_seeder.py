import os
import json
from django.core.management import call_command
from django.core.management.base import BaseCommand

def load_seeder():
    # Directorio donde están los archivos JSON
    data_dir = 'data'
    
    if not os.path.exists(data_dir):
        print('El directorio "data" no existe. Primero debes ejecutar create_seeder.py')
        return

    # Orden específico para cargar los datos
    load_order = [
        'auth_data.json',      # Primero usuarios y grupos
        'persona_data.json',   # Luego datos de personas
        'sucursales_data.json', # Luego sucursales
        'maquinas_data.json',  # Finalmente máquinas y alquileres
        'sessions_data.json'   # Y sesiones al final
    ]

    # Cargar datos en el orden especificado
    for json_file in load_order:
        file_path = os.path.join(data_dir, json_file)
        if os.path.exists(file_path):
            try:
                print(f'Cargando datos desde {json_file}...')
                call_command('loaddata', file_path, verbosity=1)
                print(f'Datos de {json_file} cargados exitosamente')
            except Exception as e:
                print(f'Error al cargar datos de {json_file}: {str(e)}')
                print('Continuando con el siguiente archivo...')
        else:
            print(f'Archivo {json_file} no encontrado, saltando...')

    print('\nProceso completado. Los datos han sido cargados en la base de datos.')

if __name__ == '__main__':
    # Configurar el entorno de Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
    import django
    django.setup()
    
    # Ejecutar la carga de datos
    load_seeder() 
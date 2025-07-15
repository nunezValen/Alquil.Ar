import os
import random
from decimal import Decimal
import string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
import django

django.setup()

# Aplicar migraciones antes de poblar
from django.core.management import call_command
call_command('migrate', interactive=False, verbosity=1)

from faker import Faker
from persona.models import Persona, Sucursal
from maquinas.models import MaquinaBase, Unidad, Alquiler
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

fake = Faker('es_ES')
Faker.seed(1234)
random.seed(1234)

# Cantidad de registros por modelo
N = 1000

IMAGE_CHOICES = [
    'maquinas/Bordeadora_a_gasolina.jpg',
    'maquinas/Compactadora_de_suelos.webp',
    'maquinas/excavadora_x300.jpg',
    'maquinas/Miniexcavadora.webp',
]


def crear_sucursales():
    sucursales = []
    for i in range(N):
        sucursales.append(
            Sucursal(
                direccion=fake.street_address(),
                latitud=random.uniform(-50, -20),
                longitud=random.uniform(-70, -40),
                telefono=fake.phone_number(),
                email=f'sucursal{i}@example.com',
                horario="L a V 8-17hs",
                es_visible=random.choice([True, False])
            )
        )
    Sucursal.objects.bulk_create(sucursales, batch_size=200)
    print(f"Se crearon {N} sucursales")


def crear_personas():
    personas = []
    for i in range(N):
        nombre = fake.first_name()
        apellido = fake.last_name()
        email = f"{nombre.lower()}.{apellido.lower()}{i}@example.com"
        personas.append(
            Persona(
                nombre=nombre,
                apellido=apellido,
                dni=str(40000000 + i),
                email=email,
                fecha_nacimiento=fake.date_of_birth(minimum_age=18, maximum_age=65),
                es_cliente=True,
            )
        )
    Persona.objects.bulk_create(personas, batch_size=200)
    print(f"Se crearon {N} personas")


def crear_maquinas_base():
    tipos = [c[0] for c in MaquinaBase.TIPOS_MAQUINA]
    marcas = [c[0] for c in MaquinaBase.MARCAS]
    maquinas = []
    for i in range(N):
        tipo = random.choice(tipos)
        marca = random.choice(marcas)
        nombre = f"{tipo.capitalize()} {i}"
        dias_min = random.randint(1, 3)
        dias_max = dias_min + random.randint(2, 10)
        maquinas.append(
            MaquinaBase(
                nombre=nombre,
                tipo=tipo,
                marca=marca,
                modelo=str(random.randint(100, 999)),
                precio_por_dia=Decimal(random.randint(1000, 10000)),
                descripcion_corta=fake.sentence(),
                descripcion_larga=fake.paragraph(),
                dias_alquiler_min=dias_min,
                dias_alquiler_max=dias_max,
                dias_cancelacion_total=10,
                dias_cancelacion_parcial=5,
                porcentaje_reembolso_parcial=50,
                visible=True,
                imagen=random.choice(IMAGE_CHOICES),
            )
        )
    MaquinaBase.objects.bulk_create(maquinas, batch_size=200)
    print(f"Se crearon {N} máquinas base")


def crear_unidades():
    sucursales = list(Sucursal.objects.all())
    maquinas = list(MaquinaBase.objects.all())
    unidades = []
    for i in range(N):
        mb = random.choice(maquinas)
        suc = random.choice(sucursales)
        patente = f"AA{i:04d}BB"
        unidades.append(
            Unidad(
                maquina_base=mb,
                patente=patente,
                sucursal=suc,
                estado='disponible',
                visible=True
            )
        )
    Unidad.objects.bulk_create(unidades, batch_size=200)
    print(f"Se crearon {N} unidades")


def crear_alquileres():
    personas = list(Persona.objects.all())
    maquinas = list(MaquinaBase.objects.all())
    inicio_num = Alquiler.objects.count() + 1  # continuar numeración si ya existen
    codigos_usados = set(Alquiler.objects.values_list('codigo_retiro', flat=True))
    alquileres = []
    for i in range(N):
        mb = random.choice(maquinas)
        persona = random.choice(personas)
        inicio = fake.date_between(start_date='-1y', end_date='today')
        fin = inicio + timezone.timedelta(days=random.randint(1, mb.dias_alquiler_max))

        # número de alquiler único A-XXXX
        numero = f"A-{(inicio_num + i):04d}"

        # código de retiro único de 8 chars
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if codigo not in codigos_usados:
                codigos_usados.add(codigo)
                break

        alquileres.append(
            Alquiler(
                numero=numero,
                codigo_retiro=codigo,
                maquina_base=mb,
                persona=persona,
                fecha_inicio=inicio,
                fecha_fin=fin,
                cantidad_dias=(fin - inicio).days + 1,
                estado='reservado',
                metodo_pago=random.choice([c[0] for c in Alquiler.METODOS_PAGO]),
                monto_total=Decimal(mb.precio_por_dia) * ((fin - inicio).days + 1)
            )
        )
    Alquiler.objects.bulk_create(alquileres, batch_size=100)
    print(f"Se crearon {N} alquileres")


def run():
    with transaction.atomic():
        crear_sucursales()
        crear_personas()
        crear_maquinas_base()
        crear_unidades()
        crear_alquileres()

if __name__ == '__main__':
    run() 
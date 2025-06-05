import random
import string

def generar_password_random():
    """
    Genera una contraseña aleatoria entre 6 y 16 caracteres.
    Incluye letras mayúsculas, minúsculas, números y caracteres especiales.
    """
    longitud = random.randint(6, 16)
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(caracteres) for _ in range(longitud))
    return password 
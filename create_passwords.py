from django.contrib.auth.hashers import make_password

passwords = {
    'mario.bro': 'MarioBro123!',
    'luigi.bro': 'LuigiBro123!'
}

for username, password in passwords.items():
    hashed = make_password(password)
    print(f"\nPara {username}:")
    print(f"Password hash: {hashed}") 
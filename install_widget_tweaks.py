import subprocess
import sys

def install_package():
    print("Installing django-widget-tweaks...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "django-widget-tweaks"])
        print("django-widget-tweaks installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing django-widget-tweaks: {e}")
        return False
    return True

if __name__ == "__main__":
    install_package()
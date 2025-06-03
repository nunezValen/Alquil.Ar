import subprocess
import sys

def install_package():
    print("Installing Pillow...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("Pillow installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Pillow: {e}")
        return False
    return True

if __name__ == "__main__":
    install_package()
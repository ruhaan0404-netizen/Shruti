import subprocess
import time

dart_folder = r"C:\Users\Rishav\Jarvis\lib\jarvis_ui"
python_folder = r"C:\Users\Rishav\Shruti\lib\shruti_backend"

def main():
    subprocess.run('start cmd /k python interact.py',shell=True,cwd=python_folder,check=True)
    time.sleep(10)
    subprocess.run('start cmd /k flutter run -d windows',shell=True,cwd=dart_folder,check=True)

if __name__=="__main__":
    main()
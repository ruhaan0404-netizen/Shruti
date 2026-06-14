import subprocess
import time

dart_folder = r"C:\Users\Rishav\Jarvis\lib\jarvis_ui"

def main():
    subprocess.run('start cmd /k python interact.py',shell=True,check=True)
    time.sleep(10)
    subprocess.run('start cmd /k flutter run -d windows',shell=True,cwd=dart_folder,check=True)

if __name__=="__main__":
    main()
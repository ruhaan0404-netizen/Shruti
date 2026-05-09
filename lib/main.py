import os

def main():
    cwd = os.getcwd()
    source = os.path.join(cwd,"calendar_script.py")
    destination = os.path.join(cwd,"lib/tools/calendar.py")
    os.rename(source,destination)

main()
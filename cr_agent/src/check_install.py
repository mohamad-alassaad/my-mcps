# check_install.py
# Lancer : python check_install.py

print("\n=== Verification MeetScribe ===\n")

packages = [
    "gradio",
    "faster_whisper",
    "soundfile",
    "numpy",
    "reportlab",
    "docx",
    "pypdf",
    "requests",
]

tous_ok = True

for package in packages:
    try:
        __import__(package)
        print("  OK       " + package)
    except ImportError:
        print("  MANQUANT " + package)
        tous_ok = False

print()
if tous_ok:
    print("Tout est installe. Pret pour l Etape 1.")
else:
    print("Packages manquants. Lancez : pip install -r requirements.txt")

print()
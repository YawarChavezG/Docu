"""SCP this file to QAS and run: python3 /tmp/extract_qas.py"""
import zipfile, os

TARGET = "/opt/sgd"
ZIP_PATH = "/tmp/sgd_deploy.zip"

# Remove problematic dirs that might conflict
for d in ["deploy/nginx/nginx.conf"]:
    p = os.path.join(TARGET, d)
    if os.path.isdir(p):
        os.rmdir(p)

# Extract
os.chdir(TARGET)
z = zipfile.ZipFile(ZIP_PATH)
z.extractall(".")
z.close()
print("EXTRACT_OK")

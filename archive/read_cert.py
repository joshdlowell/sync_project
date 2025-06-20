#!/usr/bin/python3
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID

# Assuming you have the certificate content in a variable (e.g., from a file)
# Example: cert_pem_data = open("your_certificate.pem", "rb").read()
cert_pem_data = b"""-----BEGIN CERTIFICATE-----
MIIDZTCCAk+gAwIBAgIQX/t+... (your actual certificate data) ...
-----END CERTIFICATE-----"""

with open('grafana.crt', 'rb') as f:
    cert_pem_data = f.read()

# Load the certificate
cert = x509.load_pem_x509_certificate(cert_pem_data, default_backend())

# Get the subject
subject = cert.subject

# Get the Common Name
common_name_attributes = subject.get_attributes_for_oid(NameOID.COMMON_NAME)

if common_name_attributes:
    common_name = common_name_attributes[0].value
    print(f"Common Name: {common_name}")
else:
    print("Common Name not found in the certificate subject.")
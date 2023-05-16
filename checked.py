import argparse
import os
import hashlib
from OpenSSL.crypto import load_certificate, FILETYPE_PEM, FILETYPE_ASN1
from cryptography.hazmat.primitives import serialization

# Gets thumprint of certificate (used for hash/ssl values)
def get_thumbprint(filename):
    with open(filename, 'rb') as f:
        cert_data = f.read()
    basename, extension = os.path.splitext(filename)
    if extension == '.crt' or extension == '.pem':
        cert = load_certificate(FILETYPE_PEM, cert_data)
        cert_data = cert.to_cryptography().public_bytes(encoding = serialization.Encoding.DER)
        cert_hash = hashlib.sha1(cert_data).hexdigest()
    elif extension == '.der':
        cert = load_certificate(FILETYPE_ASN1, cert_data)
        cert_data = cert.to_cryptography().public_bytes(encoding = serialization.Encoding.DER)
        cert_hash = hashlib.sha1(cert_data).hexdigest()
    return cert_hash

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Python script which calculates which values (either hashes of urls) have been checked, which of those return a result, and which do not')

# Adding arguments for the script
parser.add_argument('operation', metavar='OPERATION {SSL, URL}', help='Operation you would like to complete. Either SSL or URL', choices=[
                    'SSL', 'ssl', 'URL', 'url'])
parser.add_argument('-i', '--input', metavar='INPUT_DIR', help='Input directory of files which have been downloaded (certificate directory) - not recursive', required=True)
parser.add_argument('-o', '--output', metavar='OUTPUT_DIR', help='Output directory for text files', required=True)
parser.add_argument('-hi', '--hits', metavar='HIT_FILE', help='File containing list of values which are supposed to be downloaded', required=True)
parser.add_argument('-c', '--checked', metavar='CHECKED_FILE', help='Text file containg data that has already been queried. Used to determine which values don\'t provide a result', required=True)

# Parse the arguments
args = parser.parse_args()

# Access the arguments from the user
operation = args.operation.lower()
input_dir = args.input
output_dir = args.output
hits_file = args.hits
checked_file = args.checked

# Setting variables for output
current = 0
errors = set()

# Create the destination directory if it doesn't already exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Getting inputs
with open(checked_file, "r") as f:
    checked = f.readlines()
checked = set(x.strip() for x in checked)
with open(hits_file, "r") as f:
    hits = f.readlines()
hits = set(x.strip() for x in hits)

if operation == "ssl":
    # Gets the thumbprints/hashes of all the certificates which have been successfully downloaded
    current = 0
    found_certificates = []
    for filename in os.listdir(input_dir):
        try:
            if filename.endswith(".crt") or filename.endswith(".pem") or filename.endswith(".der"):
                # Gives feedback to user
                current += 1
                print(f"{current} certificates downloaded", end="\r")
                found_certificates.append(get_thumbprint(os.path.join(input_dir, filename)))
        except Exception as e:
            errors.add(str(e).split(':')[0])
    print(f"{current} certificates downloaded", end="\n")
    
    # Gets the thumbprints/hashes of certificates which should have been downloaded but weren't
    current = 0
    missing_hits = []
    for hash in hits:
        try:
            if hash in found_certificates:
                continue
            current += 1
            missing_hits.append(hash)
            print(f"{current} certificates which should have been downloaded", end="\r")
        except Exception as e:
            errors.add(str(e).split(':')[0])
    print(f"{current} certificates which should have been downloaded", end="\n")

        
    # Gets the thumbprints/hashes of certificates which did not return any certificates when querying crt.sh
    current = 0
    missing_certificates = []
    for hash in checked:
        try:
            if hash in hits:
                continue
            current += 1
            missing_certificates.append(hash)
            print(f"{current} hashes which did not return any certificates", end="\r")
        except Exception as e:
            errors.add(str(e).split(':')[0])
    print(f"{current} hashes which did not return any certificates", end="\n")
    
    # Writes the files to the output
    output_found = os.path.join(output_dir, "found_hash_certificates.txt")
    output_mis_hit = os.path.join(output_dir, "missing_hash_hits.txt")
    output_missing = os.path.join(output_dir, "missing_hash_certificates.txt")
    with open(output_found, 'w') as file:
        for hash in found_certificates:
            file.write(hash)
            file.write('\n')
    with open(output_mis_hit, 'w') as file:
        for hash in missing_hits:
            file.write(hash)
            file.write('\n')
    with open(output_missing, 'w') as file:
        for hash in missing_certificates:
            file.write(hash)
            file.write('\n')
elif operation == 'url':
    # Gets the urls of all the certificates which have been successfully downloaded (assuming the name is the url)
    current = 0
    found_certificates = []
    for filename in os.listdir(input_dir):
        try:
            if filename.endswith(".crt") or filename.endswith(".pem") or filename.endswith(".der"):
                # Gives feedback to user
                current += 1
                print(f"{current} certificates downloaded", end="\r")
                basename, extension = os.path.splitext(filename)
                found_certificates.append(basename)
        except Exception as e:
            errors.add(str(e).split(':')[0])
    print(f"{current} certificates downloaded", end="\n")
    
    # Gets the urls of certificates which should have been downloaded but weren't
    current = 0
    missing_hits = []
    for hash in hits:
        try:
            if hash in found_certificates:
                continue
            current += 1
            missing_hits.append(hash)
            print(f"{current} certificates which should have been downloaded", end="\r")
        except Exception as e:
            errors.add(str(e).split(':')[0])
    print(f"{current} certificates which should have been downloaded", end="\n")

        
    # Gets the thumbprints/hashes of certificates which did not return any certificates when querying crt.sh
    current = 0
    missing_certificates = []
    for hash in checked:
        try:
            if hash in hits:
                continue
            current += 1
            missing_certificates.append(hash)
            print(f"{current} hashes which did not return any certificates", end="\r")
        except Exception as e:
            errors.add(str(e).split(':')[0])
    print(f"{current} hashes which did not return any certificates", end="\n")
    
    # Writes the files to the output
    output_found = os.path.join(output_dir, "found_url_certificates.txt")
    output_mis_hit = os.path.join(output_dir, "missing_url_hits.txt")
    output_missing = os.path.join(output_dir, "missing_url_certificates.txt")
    with open(output_found, 'w') as file:
        for hash in found_certificates:
            file.write(hash)
            file.write('\n')
    with open(output_mis_hit, 'w') as file:
        for hash in missing_hits:
            file.write(hash)
            file.write('\n')
    with open(output_missing, 'w') as file:
        for hash in missing_certificates:
            file.write(hash)
            file.write('\n')
    
    
# Outputs the result of the operation
if len(errors) > 0:
    print("Unable to check all files with 100% success                                  \n")
    print("Errors encounter: ")
    for error in errors:
        print(error)
else:
    print("Successfully checkd all files                                               ")
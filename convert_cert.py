import argparse
import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Python script which converts certificate data into either CRT, PEM, or DER filetypes')

# Adding arguments for the script
parser.add_argument('-t', '--to', metavar='{der, crt, pem}', help='Specify the filetype you want to convert FROM', required=True, choices=['der', 'pem', 'crt', 'DER', 'PEM', 'CRT'])
parser.add_argument('-f', '--from', metavar='{der, crt, pem}', dest='_from', help='Specify the filetype you want to convert TO', required=True, choices=['der', 'pem', 'crt', 'DER', 'PEM', 'CRT'])
parser.add_argument('-i', '--input', metavar='INPUT_DIR', help='Input directory of original files', required=True)
parser.add_argument('-o', '--output', metavar='OUTPUT_DIR', help='Output directory of converted files', required=True)

# Parse the arguments
args = parser.parse_args()

# Access the arguments from the user
to_filetype = '.'+args.to.lower()
from_filetype = '.'+args._from.lower()
input_dir = args.input
output_dir = args.output

# Setting variables for output
total = len(os.listdir(input_dir))
current = 0
errors = set()

# Create the destination directory if it doesn't already exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Loop through all files in the source directory and convert the files accordingly
for file_name in os.listdir(input_dir):
    # Gives feedback to user
    current += 1
    print(f"Processing item {current} / {total} ", end="\r")
    
    # Create the source file path
    file_path = os.path.join(input_dir, file_name)
    
    # Check if the file is a regular file and has the correct extension
    if os.path.isfile(file_path) and file_name.endswith(from_filetype):
        try:
            # Create the destination file path with the correct extension
            output_file = os.path.join(output_dir, os.path.splitext(file_name)[0] + to_filetype)
            
            with open(file_path, "rb") as file:
                # Reading data from current file
                file_data = file.read()
                
                if from_filetype == '.pem' or from_filetype == '.crt':
                    old_data = x509.load_pem_x509_certificate(file_data, default_backend())
                elif from_filetype == '.der':
                    old_data = x509.load_der_x509_certificate(file_data, default_backend())
                
                # Create file from old data
                if to_filetype == ".pem":
                    new_data = old_data.public_bytes(encoding=serialization.Encoding.PEM)
                elif to_filetype == ".der":
                    new_data = old_data.public_bytes(encoding=serialization.Encoding.DER)
                elif to_filetype == ".crt":
                    new_data = old_data.public_bytes(encoding=serialization.Encoding.PEM)
                    
                # Writes the new file to the correct output directory
                with open(output_file, "wb") as out_file:
                    out_file.write(new_data)
        except Exception as e:
            errors.add(str(e).split(':')[0])

# Outputs the result of the operation
if len(errors) > 0:
    print("Unable to convert all queries with 100% success                                  \n")
    print("Errors encounter: ")
    for error in errors:
        print(error)
else:
    print("Successfully convert all files                                               ")

import argparse
import os
import shutil

# Initialize the argument parser
parser = argparse.ArgumentParser(description='Python script which changes the extensions of files CRT, PEM, or DER')

# Adding arguments for the script
parser.add_argument('-t', '--to', metavar='{der, crt, pem}', help='Specify the extension you want to convert FROM', required=True, choices=['der', 'pem', 'crt', 'DER', 'PEM', 'CRT'])
parser.add_argument('-f', '--from', metavar='{der, crt, pem}', dest='_from', help='Specify the extension you want to convert TO', required=True, choices=['der', 'pem', 'crt', 'DER', 'PEM', 'CRT'])
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

# Iterate over the files in the source directory
for filename in os.listdir(input_dir):
    # Gives feedback to user
    current += 1
    print(f"Processing item {current} / {total} ", end="\r")
    try:
        # Check if the file has a .crt extension
        if filename.endswith(from_filetype):
            # Build the source and destination file paths
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + to_filetype)
    
            # Copy the file to the destination directory
            shutil.copy(input_path, output_path)
    except Exception as e:
        errors.add(str(e).split(':')[0])

# Outputs the result of the operation
if len(errors) > 0:
    print("Unable to convert all files with 100% success                                  \n")
    print("Errors encounter: ")
    for error in errors:
        print(error)
else:
    print("Successfully convert all files                                               ")

import argparse
import os
import requests
import re
import socket
import ssl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Checks if the input argument is a positive value
def positive_float(value):
    fvalue = float(value)
    if fvalue <= 0:
        raise argparse.ArgumentTypeError("%s is not a positive float" % value)
    return fvalue

# Adds a value to the checked file - keeps track of the checked values in case program crashes
def add_checked(filename, value):
    with open(filename, "a") as file:
        file.write(value)
        file.write("\n")

# Initialize the argument parser
parser = argparse.ArgumentParser(
    description='Python script which automatically gets certificates')

# Adding arguments for the script
parser.add_argument('operation', metavar='OPERATION {SSL, URL}', help='Operation you would like to complete. Either SSL or URL', choices=[
                    'SSL', 'ssl', 'URL', 'url'])
parser.add_argument('-i', '--input', metavar='INPUT_FILE',
                    help='Text file containing data to query. Not specified will just use the list on abuse.ch - either SSLBL or URLHAUS', required=False)
parser.add_argument('-c', '--checked', metavar='CHECKED_FILE',
                    help='Text file containg data that has already been queried. This data will be ignored if it is in the INPUT_LIST. Not specified will scan all results and will create a file to keep track of checked queries', required=False)
parser.add_argument('-t', '--timeout', metavar='TIMEOUT',
                    help='Maximum time spent before moving on to the next data point. Grace period before program moves on', required=False, type=positive_float)
parser.add_argument('-s', '--secure', action='store_true', 
                    help='Setting this argument will ensure that only valid SSL certificates are downloaded from the URLs (i.e. no self signed certificates or mismathcing names will be downloaded). Default = False', required=False, default=False)
parser.add_argument('-v', '--verbose', action='store_true', 
                    help='Debug mode. Default = False', required=False, default=False)
parser.add_argument('-o', '--output', metavar='OUTPUT_DIR',
                    help='Directory where queries are stored. Must specify this argument LAST. For SSL downloads will be put in Downloads folder', required=True)

# Parse the arguments
args = parser.parse_args()

# Check for conditional arguments
if args.operation.lower() != 'url' and args.secure:
    parser.error('Secure is only applicable for operation "url"')

# Access the arguments from the user
operation = args.operation.lower()
input_file = args.input
checked_file = args.checked
output_dir = args.output
timeout = args.timeout
secure = args.secure
debug = args.verbose

# Setting variables for output
total = -1  # Set later
current = 0
errors = set()

# Create the destination directory if it doesn't already exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Gets the checked queries
if checked_file == None:
    checked = set()
    output_filename = output_dir.split('\\')[-1]
    checked_file = "./checked_data_going_to_"+output_filename+".txt"
else:
    with open(checked_file, "r") as f:
        checked = f.readlines()
    checked = set(x.strip() for x in checked)

# Complete the operation has specified by the user
# SSL will query SSL hashes using the crt.sh website
if operation == 'ssl':
    if timeout == None:
        timeout = 5
        
    # Setting download directory - this feature may not work
    download_directory = output_dir

    # Creating chrome web broswer and setting configuration (which allow the download of certificates)
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Hides windows
    # chrome_options.add_argument("--incognito") # Incognitio mode
    prefs = {
        "download.default_directory": download_directory,
        "download.propmt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--safebrowsing-disable-extension-blacklist")
    chrome_options.add_argument("--safebrowsing-disable-download-protection")
    service = Service("./chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, timeout)

    hashes = []
    # Gets HASHES for abuse.ch if an input isn't provided
    if input_file == None:
        # Get the most up to date SSLBL list from abuse.ch and parses it
        contents = requests.get(
            "https://sslbl.abuse.ch/blacklist/sslblacklist.csv").text

        pattern1 = r"^[^,]*"
        pattern2 = r"[^,]*$"
        pattern3 = r","
        new_contents = re.sub(pattern1, "", contents, flags=re.MULTILINE)
        new_contents = re.sub(pattern2, "", new_contents, flags=re.MULTILINE)
        new_contents = re.sub(pattern3, "", new_contents, flags=re.MULTILINE)

        all_hashes = list(set(new_contents.splitlines()[1:]))
        for hash in all_hashes:
            if hash.strip() in checked:
                continue
            hashes.append(hash.strip())
    # Gets hashes from input file provided
    else:
        with open(input_file, 'r') as f:
            all_hashes = f.readlines()
        for hash in all_hashes:
            if hash.strip() in checked:
                continue
            hashes.append(hash.strip())
    
    # Goes to crt.sh
    url = "https://crt.sh/"
    driver.get(url)
    total = len(hashes)
    processed = 0
    
    # Get the certificate of each hash (if it exists in the crt.sh database)
    while len(hashes) > 0:
        # Gives feedback to user
        current += 1
        if not debug:
            print(f"{current} number of total requests made. Processed {processed} / {total} items", end="\r")
        
        # Pre-logic actions (wait, set, check)
        time.sleep(1)
        hash = hashes.pop(0)
        if hash in checked:
            continue
        if debug:
            print(f"\nChecking hash: {hash}")
        
        # Tries to find the search bar and inputs the hash (clear it from previous state)
        try:
            search_input = driver.find_elements(By.CLASS_NAME, "input")[0]
            search_input.clear()
            search_input.send_keys(hash)
            search_button = driver.find_elements(By.CLASS_NAME, "button")[0]
            search_button.click()
        except Exception as e:
            if debug:
                print(e)
            # If the search bar cannot be found it is likley we are on the wrong page
            errors.add(str(e).split(':')[0])
            hashes.append(hash)
            time.sleep(timeout/2)
            driver.get(url)
            time.sleep(timeout/2)
            continue

        try:
            # Wait for body to load
            body_content = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            
            # Get body content which can be in three states - certificate exists, certificate doesn't exist,
            # or page did not load corrently (either 502 or database query time limit exceeded)
            body_content = driver.page_source

            # Cannot download a certificate
            if "Certificate not found" in body_content:
                processed += 1
                add_checked(checked_file, hash)                    
                driver.back()
                if debug:
                    print('Certificate not found')
            # Body content loaded
            else:
                # Successfully found certificate
                try:
                    download_text = "PEM"
                    download_link = driver.find_elements(By.LINK_TEXT, download_text)[0]
                    download_link.click()
                    time.sleep(1) #wait for download
                    driver.back()
                    add_checked("./hash_hits.txt", hash) # Occasionnally the download takes to long and doesn't get made. So saving "hits" can be used to compare hits vs the actual number of downloaded files
                    add_checked(checked_file, hash)
                    processed += 1
                    if debug:
                        print('Downloaded successfully')
                # Error page has loaded
                except Exception as e:
                    if debug:
                        print(e)
                    errors.add(str(e).split(':')[0])
                    hashes.append(hash)
                    time.sleep(timeout)
                    driver.back()
        # Page didn't load in specified time
        except TimeoutError as e:
            if debug:
                print(e)
            errors.add(str(e).split(':')[0])
            hashes.append(hash)
            driver.back()

# URL will query websites for their certificate
elif operation == 'url':
    if input_file == None:
        # Get the most up to date URLHAUS list from abuse.ch and parsing data
        contents = requests.get(
            "https://urlhaus.abuse.ch/downloads/text/").text

        pattern1 = r"(https?://)"
        pattern2 = r"\/[^\n]*"
        pattern3 = r":[^\n]*"
        pattern4 = r"#[^\n]*"
        pattern5 = r"^\s*\n"
        new_contents = re.sub(pattern1, "", contents)
        new_contents = re.sub(pattern2, "", new_contents)
        new_contents = re.sub(pattern3, "", new_contents)
        new_contents = re.sub(pattern4, "", new_contents)
        new_contents = re.sub(pattern5, "", new_contents, flags=re.MULTILINE)

        all_urls = list(new_contents.splitlines())
    else:
        # Opens and reads the file as specified by user to use as urls
        with open(input_file, "r") as f:
            all_urls = f.readlines()
        all_urls = list(all_urls)

    # Removes checked urls from urls list
    unchecked_urls = []
    for url in all_urls:
        if url.strip() in checked:
            continue
        unchecked_urls.append(url.strip())
    urls = unchecked_urls

    # Creating variables for feedback and usage
    total = len(urls)
    if timeout == None:
        timeout = 1
        
    # Set the default timeout for socket operations
    socket.setdefaulttimeout(timeout)
        
    # Create a context object and set the verification flags
    context = ssl.create_default_context()
    if secure:
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    for url in urls:
        # Gives feedback to user
        current += 1
        if not debug:
            print(f"Processing item {current} / {total} ", end="\r")

        # Track if URL checked successfully
        success = True
        
        if debug:
            print(f"\nChecking url: {url}")

        # Format data
        url = url.strip()
        output_location = os.path.join(output_dir, f"{url}.der")

        # Queries URL for certificate and saves it if recieved
        try:
            with ssl.create_connection((url, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=url) as sslsock:
                    cert = sslsock.getpeercert(binary_form=True)
                    with open(output_location, "wb") as output_file:
                        if debug:
                            print('Downloaded successfully')
                        output_file.write(cert)
                    add_checked("./url_hits.txt", url) # Occasionnally the download takes to long and doesn't get made. So saving "hits" can be used to compare hits vs the actual number of downloaded files
        except Exception as e:
            if debug:
                print(e)
            errors.add(str(e).split(':')[0])
            pass

        # Updates the checked file
        if success:
            add_checked(checked_file, url)

# Outputs the result of the operation
if not debug:
    if len(errors) > 0:
        print("Unable to make all queries with 100% success                                  \n")
        print("Errors encounter: ")
        for error in errors:
            print(error)
    else:
        print("Successfully made all queries                                               ")

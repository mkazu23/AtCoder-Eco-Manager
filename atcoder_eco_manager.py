import requests
from bs4 import BeautifulSoup
import os
import time
import glob
import json
import copy
import re


# Your Atcoder username
USERNAME = os.getenv('ATCODER_USERNAME')

# ATCODER_PROBLEMS_URL
ATCODER_PROBLEMS_URL = f'https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={USERNAME}&from_second={0}'


# File path for timestamp information
RECORDED_TIMESTAMP_FILE = 'recorded_timestamp.json'

# Set the headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'From': 'you@example.com'
}

# Set the extensions
EXTENSIONS = {
    r"\bC\+\+": "cpp", 
    "Bash": "sh",
    "C#": "cs",
    "JavaScript": "js",
    "OpenJDK": "java",
    "Haskell": "hs",
    "OCaml": "ml",
    "Perl": "pl",
    "PHP": "php",
    r"Python|Cpython|PyPy": "py",
    "Pascal": "pas",
    "Perl": "pl",
    "Ruby": "rb",
    "Scala": "scala",
    "Visual Basic": "vb",
    "Objective-C": "m",
    "Swift": "swift",
    "Rust": "rs",
    "Sed": "sed",
    "Awk": "awk",
    "Brainfuck": "bf",
    "Standard ML": "ml",
    "Crystal": "cr",
    "Julia": "jl",
    "Octave": "m",
    "Nim": "nim",
    "TypeScript": "ts",
    "Perl6": "p6",
    "Kotlin": "kt",
    "COBOL": "cob",
    "C": ".c",
}


# Start session
session = requests.Session()

def load_recorded_timestamp():
    """_summary_
    Load saved timestamp information from a file

    Returns:
        dict: Dictionary containing the saved timestamp information
    """
    if os.path.exists(RECORDED_TIMESTAMP_FILE):
        with open(RECORDED_TIMESTAMP_FILE, 'r') as file:
            return json.load(file)
    else:
        default_data = {}
        with open(RECORDED_TIMESTAMP_FILE, 'w') as file:
            json.dump(default_data, file)
        return default_data

def save_recorded_timestamp(latest_timestamp):
    """_summary_
    Save the latest timestamp information to a file.

    Args:
        dict: Dictionary holding the id of the problem and the latest timestamp information.
    """

    with open(RECORDED_TIMESTAMP_FILE, 'w') as file:
        json.dump(latest_timestamp, file)

        
def fetch_ac_submissions():
    """_summary_
    Get submissions that are AC (Accepted) and return the latest results.

    Returns:
        tuple:  (List of the latest submission results, Tuple of the timestamp information)
    """
     # Dictionary for getting the latest AC codes
    latest_ac = {}

    # Initialize list for timestamp information
    timestampInfo = []

    # Flag indicating whether timestamp needs to be updated
    should_update_timestamp = False

    try:
        # Get submission information
        response = session.get(ATCODER_PROBLEMS_URL)
        response.raise_for_status
        submissions = response.json()

        # Extract only submissions that are AC and latest by time, store them in a dictionary
        ac_submissions = {}
        for submission in submissions:
            if submission['result'] == "AC":
                problem_id = submission['problem_id']
                if problem_id not in ac_submissions or submission['epoch_second'] > ac_submissions[problem_id]['epoch_second']:
                    ac_submissions[problem_id] = submission
        

        ac_submissions = list(ac_submissions.values())

        # Load saved timestamp information and create a copy
        recorded_timestamp = load_recorded_timestamp()
        latest_timestamp = copy.deepcopy(recorded_timestamp)

        # Update the latest AC codes
        for submission in ac_submissions:
            key = (submission['contest_id'], submission['problem_id'], submission['id'])
            if key not in latest_ac or submission['epoch_second'] > latest_ac[key]['epoch_second']:
                latest_ac[key] = submission

        # Compare timestamp information to decide if an update is needed
        for key, val in latest_ac.items():
            if val['epoch_second'] > recorded_timestamp.get(key[1],0) or key[1] not in recorded_timestamp:
                latest_timestamp[key[1]] = val['epoch_second']
                should_update_timestamp = True

        # Return the timestamp information as a tuple
        timestamp_info = (recorded_timestamp, latest_timestamp, should_update_timestamp)
        return latest_ac, timestamp_info

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def fetch_submission_info(contest_id, id):
    """_summary_
    Fetch code and problem information for given contest ID and submission ID.

    Args:
        contest_id (_type_): Contest id
        id (_type_): Problem id

    Returns:
        dictionary: Contains the code、problem title、and problem URL.
    """
    try:
        # Construct the submission page URL
        sub_url = f"https://atcoder.jp/contests/{contest_id}/submissions/{id}"
        print("sub_url",sub_url)

        # Insert a moderate sleep to reduce server load
        time.sleep(3)

        # Fetch HTML of the submission page
        response = session.get(sub_url)
        response.raise_for_status()

        if response.ok:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            code_element = soup.find('pre', id='submission-code')
            source_code = code_element.text

            problem_info = soup.find('a', href=lambda href: href and 'tasks/' in href)
            problem_url = f"https://atcoder.jp{problem_info['href']}"
            problem_title = problem_info.get_text(strip=True)

            return {
                'source_code': source_code,
                'problem_title': problem_title,
                'problem_url': problem_url
            }

        else:
            print(f"Failed to access submission page. HTTP status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def modify_filename(filename):
    """_summary_
    Replace special characters with underscores and shorten the filename

    Args:
        filename (str): Filename to be replaced
    Returns:
        str: Filename with special characters replaced by underscores
    """
    filename = re.sub(r'[\\\/:*?"<>|]', '_', filename)
    return filename

def get_file_extension(language):
    """_summary_
    Selects the file extension from the language name based on mapping.

    Args:
        language (str): The name of the programming language.
    Returns:
        str: The file extension corresponding to the language, or None if not found.
    """
    for lang, ext in EXTENSIONS.items():
        if re.search(lang, language, re.IGNORECASE):
            return ext
    return None


def create_files(ac_submissions, timestamp_info):
    """_summary_
    Save code and problem information of AC submissions to files

    Args:
        ac_submissions (dict): Dictionary containing AC submission information
        timestamp_info (tuple): Tuple of timestamp information
    """

    for (contest_id, problem_id, id), submission in ac_submissions.items():
        
        # Skip if the timestamp matches
        if timestamp_info[0].get(problem_id) == submission['epoch_second']:
            continue
        
        # Fetch submission details
        submission_details = fetch_submission_info(contest_id, id)
        
        language = submission['language']
        extension = get_file_extension(language)

        # Create directory to save the files
        directory = f'./submissons/{contest_id}/{problem_id}'
        if not os.path.exists(directory):
            os.makedirs(directory)

        problem_title = modify_filename(submission_details['problem_title'])

        # Save the code as .py file
        source_filename = os.path.join(directory, f"{problem_title}.{extension}")

        with open(source_filename, 'w') as source_file:
            source_file.write(submission_details['source_code'])

        # Save problem title and URL in a text file
        title_filename = os.path.join(directory, f"{problem_title}.md")

        title_content = f"Link : [{problem_title}]({submission_details['problem_url']})"

        with open(title_filename, 'w') as text_file:
            text_file.write(title_content)

    # Save the latest timestamp information if needed
    if timestamp_info[2]:
        save_recorded_timestamp(timestamp_info[1])

if __name__ == '__main__':
    ac_submissions, timestamp_info = fetch_ac_submissions()
    create_files(ac_submissions, timestamp_info)
    print("Done")
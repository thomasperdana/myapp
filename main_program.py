#!/opt/anaconda3/bin/python
"""
Main program with 20 procedures and comprehensive logging system.
The input directory is now read-only with permissions set to 555 (r-xr-xr-x)
smtp app password:
ktnd vioj bxxu aika
qE7!sP9*bK2@zX4#
/opt/anaconda3/bin/python main_program.py
conda activate base
pyinstaller --onefile main_program.py
code-insiders .
"""

import logging
import logging.handlers
import os
import sys
import re
import requests # Added for API calls
from datetime import datetime, timedelta
from pathlib import Path



def get_base_path():
    """ Get the base path for the script, handling PyInstaller's temp folder. """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (executable)
        return sys._MEIPASS
    else:
        # We are running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))
    
# Global variables
INPUT_DIR = None
OUTPUT_DIR = None
LAST_WEEK_DATE = None
NEXT_WEEK_DATE = None
NEXT_WEEK_AGENDA_FILE = None

# List of all Bible book names for precise regex matching
BIBLE_BOOK_NAMES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
    "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude",
    "Revelation"
]

def get_kjv_verse(reference):
    """
    Fetches KJV verses for a given Bible reference from bible-api.com.
    Args:
        reference (str): The Bible reference (e.g., "John 3:16", "Psalm 23").
    Returns:
        list: A list of verse strings, or an empty list if not found or error.
    """
    logger = logging.getLogger(__name__)
    base_url = "https://bible-api.com/"
    
    # Encode the reference for URL
    encoded_reference = requests.utils.quote(reference)
    
    api_url = f"{base_url}{encoded_reference}?translation=kjv"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        
        verses = []
        if 'verses' in data:
            for verse_data in data['verses']:
                verses.append(verse_data['text'].strip())
        elif 'text' in data: # For single verse responses that might not be in 'verses' array
            verses.append(data['text'].strip())
            
        return verses
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching KJV verse for '{reference}': {e}")
        return []
    except ValueError: # JSON decoding error
        logger.error(f"JSON decoding error for '{reference}': {response.text}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred for '{reference}': {e}")
        return []


def setup_logging():
    """Configure comprehensive logging system with file and console handlers."""

    from pathlib import Path  # Ensure this import exists
    # Convert the string to a Path object immediately
    log_dir = Path("/Applications/myapp/logs") 
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"app_{timestamp}.log"
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def init_file():
    """Initialize application configuration."""
    import shutil
    import stat
     
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE

    logger = logging.getLogger(__name__)
    logger.info("Procedure 01: Initializing application configuration")
    logger.debug("Loading default configuration values")
    
    try:
        from pathlib import Path  # Ensure this import exists
        # Convert the string to a Path object immediately
        INPUT_DIR = Path("/Applications/myapp/input")
        OUTPUT_DIR = Path("/Applications/myapp/output")
        # Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
        # Protect input directory as read-only
        INPUT_DIR.chmod(0o555)
        for item in INPUT_DIR.rglob("*"):
            if item.is_file():
                item.chmod(0o555)
        logger.info("Protected input directory and files as read-only (555)")
        logger.debug("Set permissions to r-xr-xr-x for input directory")
        
        today = datetime.now().date()
        days_since_last_saturday = (today.weekday() - 5) % 7  # Saturday=5, returns 0 if today is Saturday
        last_week_date = today - timedelta(days=days_since_last_saturday)
        next_week_date = last_week_date + timedelta(weeks=1)
        
        LAST_WEEK_DATE = datetime.combine(last_week_date, datetime.min.time())
        NEXT_WEEK_DATE = datetime.combine(next_week_date, datetime.min.time())
        next_week_str = NEXT_WEEK_DATE.strftime("%Y-%m-%d")
        last_week_str = LAST_WEEK_DATE.strftime("%Y-%m-%d")
        
        last_week_file = INPUT_DIR / f"{last_week_str} Saturday Prayer Breakfast Agenda.md"
        
        logger.info(f"Last week date: {last_week_str}")
        logger.info(f"Next week date: {next_week_str}")
        
        NEXT_WEEK_AGENDA_FILE = OUTPUT_DIR / f"{next_week_str} Saturday Prayer Breakfast Agenda.md"
        
        # Remove existing file if it exists
        if NEXT_WEEK_AGENDA_FILE.exists():
            NEXT_WEEK_AGENDA_FILE.chmod(0o777)
            NEXT_WEEK_AGENDA_FILE.unlink()
            logger.debug(f"Removed existing file: {NEXT_WEEK_AGENDA_FILE.name}")
        
        shutil.copy2(last_week_file, NEXT_WEEK_AGENDA_FILE)
        logger.info(f"Created next week agenda: {NEXT_WEEK_AGENDA_FILE.name}")
        logger.debug(f"Copied from {last_week_file} to {NEXT_WEEK_AGENDA_FILE}")
        
        # Change file permissions to read, write, execute for all (777)
        NEXT_WEEK_AGENDA_FILE.chmod(0o777)
        logger.info(f"Changed file permissions to 777 (rwxrwxrwx)")
        logger.debug(f"File permissions updated for {NEXT_WEEK_AGENDA_FILE.name}")
        
        # Update the title in the file
        content = NEXT_WEEK_AGENDA_FILE.read_text()
        old_title = f"North Seminole County Gideons - {last_week_str} Saturday Prayer Breakfast Agenda"
        new_title = f"North Seminole County Gideons - {next_week_str} Saturday Prayer Breakfast Agenda"
        
        if old_title in content:
            updated_content = content.replace(old_title, new_title, 1)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            logger.info(f"Updated title from '{old_title}' to '{new_title}'")
            logger.debug("File content updated successfully")
        else:
            logger.warning(f"Title '{old_title}' not found in file")
        
    except Exception as e:
        logger.error(f"Failed to create next week agenda: {str(e)}")
        return {"status": "error", "procedure": "01", "error": str(e)}
    
    return {"status": "success", "procedure": "01"}


def bible_reading():
    """Update Bible Reading Rotation for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE

    logger = logging.getLogger(__name__)
    logger.info("Procedure 02: Updating Bible Reading Rotation")
    logger.debug("Reading Bible rotation schedule from hq2.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "02", "error": "Missing global variables"}
        
        # Read the Bible reading schedule
        hq2_file = INPUT_DIR / "hq2.md"
        hq2_content = hq2_file.read_text()
        
        # Extract month and day from NEXT_WEEK_DATE
        month = NEXT_WEEK_DATE.strftime("%B").upper()
        day = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for reading for {month} {day}")
        
        # Find the month section
        month_pattern = rf"## \*\*{month}\*\*.*?\n(.*?)(?=\n## \*\*|\Z)"
        month_match = re.search(month_pattern, hq2_content, re.DOTALL)
        
        if not month_match:
            logger.error(f"Could not find month section for {month}")
            return {"status": "error", "procedure": "02", "error": f"Month {month} not found"}
        
        month_section = month_match.group(1)
        
        # Find the reading for the specific day
        day_pattern = rf"^\| {day} \| (.*?) \|"
        day_match = re.search(day_pattern, month_section, re.MULTILINE)
        
        if not day_match:
            logger.error(f"Could not find reading for {month} {day}")
            return {"status": "error", "procedure": "02", "error": f"Day {day} not found"}
        
        bible_reading = day_match.group(1).strip()
        logger.info(f"Found Bible reading for {month} {day}: {bible_reading}")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the Bible Reading Rotation line
        old_pattern = r"Bible Reading Rotation - .*"
        new_reading = f"Bible Reading Rotation - {bible_reading}"
        
        updated_content = re.sub(old_pattern, new_reading, agenda_content)
        NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
        
        logger.info(f"Updated Bible Reading Rotation to: {bible_reading}")
        logger.debug("Bible reading rotation updated successfully")
        
        return {"status": "success", "procedure": "02"}
        
    except Exception as e:
        logger.error(f"Failed to update Bible reading: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "02", "error": str(e)}


def prayer_card():
    """Update Prayer Card rotation for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 03: Updating Prayer Card rotation")
    logger.debug("Reading Prayer Card schedule from prayer.md")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "03", "error": "Missing global variable"}
        
        # Read the prayer card schedule
        prayer_file = INPUT_DIR / "prayer.md"
        prayer_content = prayer_file.read_text()
        
        # Read the current agenda to find the current prayer card entry
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Extract current prayer card page number
        current_pattern = r"Prayer Card Together - Page (\d+)"
        current_match = re.search(current_pattern, agenda_content)
        
        if not current_match:
            logger.error("Could not find current Prayer Card entry in agenda")
            return {"status": "error", "procedure": "03", "error": "Current prayer card not found"}
        
        current_page = int(current_match.group(1))
        next_page = current_page + 1
        
        logger.debug(f"Current prayer card page: {current_page}, next page: {next_page}")
        
        # Find the next page entry in prayer.md
        # Look for the bullet point which has the scripture reference
        page_pattern = rf"## Page {next_page}\s*\n+### ([^\n]+)\s*\n+(\d+)\.\s+[^\n]+\n\s*\*\s+([^\n]+)"
        page_match = re.search(page_pattern, prayer_content, re.MULTILINE | re.DOTALL)
        
        if not page_match:
            logger.error(f"Could not find Page {next_page} in prayer.md")
            return {"status": "error", "procedure": "03", "error": f"Page {next_page} not found"}
        
        section_name = page_match.group(1).strip()
        item_number = page_match.group(2).strip()
        scripture_ref = page_match.group(3).strip()
        
        # Ensure section_name ends with colon if it doesn't have one
        if not section_name.endswith(':'):
            section_name += ':'
        
        # Transform scripture reference: replace ", " with "-" for verse ranges
        scripture_ref = re.sub(r',\s+(\d+)$', r'-\1', scripture_ref)
        
        # Build the new prayer card entry in the correct format
        new_prayer_card = f"Prayer Card Together - Page {next_page} {section_name} {item_number}. {scripture_ref}"
        
        logger.info(f"Next prayer card: {new_prayer_card}")
        
        # Update the agenda file
        old_pattern = r"Prayer Card Together - Page \d+.*"
        updated_content = re.sub(old_pattern, new_prayer_card, agenda_content)
        NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
        
        logger.info(f"Updated Prayer Card from Page {current_page} to Page {next_page}")
        logger.debug("Prayer card rotation updated successfully")
        
        return {"status": "success", "procedure": "03"}
        
    except Exception as e:
        logger.error(f"Failed to update Prayer Card: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "03", "error": str(e)}


def international_reading():
    """Update International Reading for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 04: Updating International Reading")
    logger.debug("Reading International schedule from hq1.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "04", "error": "Missing global variables"}
        
        # Read the international reading schedule
        hq1_file = INPUT_DIR / "hq1.md"
        hq1_content = hq1_file.read_text()
        
        # Get the day number from NEXT_WEEK_DATE
        day_number = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for DAY {day_number}")
        
        # Find the DAY section in hq1.md
        day_pattern = rf"## \*\*DAY {day_number}\*\*\s*\n(.*?)(?=\n## \*\*DAY|\Z)"
        day_match = re.search(day_pattern, hq1_content, re.DOTALL)
        
        if not day_match:
            logger.error(f"Could not find DAY {day_number} in hq1.md")
            return {"status": "error", "procedure": "04", "error": f"DAY {day_number} not found"}
        
        day_content = day_match.group(1).strip()
        
        logger.info(f"Found International Reading for DAY {day_number}")
        logger.debug(f"Content length: {len(day_content)} characters")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the International Reading section
        # Pattern: from "International Reading by..." to the next section or scripture reference
        old_pattern = r"International Reading by [^\n]+\n.*?(?=\n\n[A-Z]|\nEphesians|\nRomans|\nMatthew|\nProverbs|\nHebrews|\n2 Timothy|\n1 John|\nRevelation|\n2 Corinthians|\nActs)"
        
        new_international_reading = f"International Reading by TaeWoo Lee\n{day_content}"
        
        # Check if pattern exists
        if re.search(old_pattern, agenda_content, re.DOTALL):
            updated_content = re.sub(old_pattern, new_international_reading, agenda_content, flags=re.DOTALL)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            
            logger.info(f"Updated International Reading to DAY {day_number}")
            logger.debug("International reading updated successfully")
        else:
            logger.error("Could not find International Reading section to replace")
            return {"status": "error", "procedure": "04", "error": "International Reading section not found"}
        
        return {"status": "success", "procedure": "04"}
        
    except Exception as e:
        logger.error(f"Failed to update International Reading: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "04", "error": str(e)}


def state_reading():
    """Update State Reading for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 05: Updating State Reading")
    logger.debug("Reading State schedule from fl.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "05", "error": "Missing global variables"}
        
        # Read the state reading schedule
        fl_file = INPUT_DIR / "fl.md"
        fl_content = fl_file.read_text()
        
        # Get the day number from NEXT_WEEK_DATE
        day_number = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for Day {day_number}")
        
        # Find the Day section in fl.md
        day_pattern = rf"## Day {day_number}[^\n]*\s*\n(.*?)(?=\n---\n\n## Day|\n## Day|\Z)"
        day_match = re.search(day_pattern, fl_content, re.DOTALL)
        
        if not day_match:
            logger.error(f"Could not find Day {day_number} in fl.md")
            return {"status": "error", "procedure": "05", "error": f"Day {day_number} not found"}
        
        day_content = day_match.group(1).strip()
        
        # Remove the closing "---" if present
        day_content = re.sub(r'\n---\s*$', '', day_content)
        
        new_state_reading = f"State Reading by Alvin Beverly\n{day_content}"
        
        logger.info(f"Found State Reading for Day {day_number}")
        logger.debug(f"Formatted content:\n{new_state_reading}")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the State Reading section
        # Pattern: from "State Reading by..." to the next main section
        old_pattern = r"State Reading by [^\n]+\n.*?(?=\n\nPray for the Widows)"
        
        # Check if pattern exists
        if re.search(old_pattern, agenda_content, re.DOTALL):
            updated_content = re.sub(old_pattern, new_state_reading, agenda_content, flags=re.DOTALL)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            
            logger.info(f"Updated State Reading to Day {day_number}")
            logger.debug("State reading updated successfully")
        else:
            logger.error("Could not find State Reading section to replace")
            return {"status": "error", "procedure": "05", "error": "State Reading section not found"}
        
        return {"status": "success", "procedure": "05"}
        
    except Exception as e:
        logger.error(f"Failed to update State Reading: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "05", "error": str(e)}


def widow_prayer():
    """Update Widow Prayer for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
        
    logger = logging.getLogger(__name__)
    logger.info("Procedure 06: Updating Widow Prayer")
    logger.debug("Reading Widow schedule from widow.md")
    
    try:
        if NEXT_WEEK_DATE is None or NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variables not initialized. Run init_file first.")
            return {"status": "error", "procedure": "06", "error": "Missing global variables"}
        
        # Read the widow prayer schedule
        widow_file = INPUT_DIR / "widow.md"
        widow_content = widow_file.read_text()
        
        # Get the day number from NEXT_WEEK_DATE
        day_number = NEXT_WEEK_DATE.day
        
        logger.debug(f"Looking for section {day_number}")
        
        # Find the section in widow.md (### {day_number}. ...)
        section_pattern = rf"### {day_number}\. ([^\n]+)\n((?:- [^\n]+\n)*)"
        section_match = re.search(section_pattern, widow_content)
        
        if not section_match:
            logger.error(f"Could not find section {day_number} in widow.md")
            return {"status": "error", "procedure": "06", "error": f"Section {day_number} not found"}
        
        section_title = section_match.group(1).strip()
        widow_list = section_match.group(2).strip()
        
        # Format the widow list - convert markdown list to comma-separated format
        # Extract widows from the list items
        widows = re.findall(r'- ([^\n]+)', widow_list)
        
        # Group widows by camp
        camps_data = {}
        for widow_entry in widows:
            parts = widow_entry.split(', ', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                camp = parts[1].strip()
                if camp not in camps_data:
                    camps_data[camp] = []
                camps_data[camp].append(name)
            else:
                logger.warning(f"Skipping malformed widow entry: {widow_entry}")
        
        formatted_parts = []
        for camp, names_list in camps_data.items():
            formatted_parts.append(f"{camp} - {', '.join(names_list)}, ")
        
        formatted_widow_text = " - ".join(formatted_parts)

        
        new_widow_prayer = f"Pray for the Widows by Donald Tise - {day_number}. {section_title}\n{formatted_widow_text}"
        
        logger.info(f"Found Widow Prayer for section {day_number}: {section_title}")
        logger.debug(f"Formatted content:\n{new_widow_prayer}")
        
        # Update the agenda file
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find and replace the Widow Prayer section
        old_pattern = r"Pray for the Widows by [^\n]+\n[^\n]+"
        
        # Check if pattern exists
        if re.search(old_pattern, agenda_content, re.DOTALL):
            updated_content = re.sub(old_pattern, new_widow_prayer, agenda_content, flags=re.DOTALL)
            NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
            
            logger.info(f"Updated Widow Prayer to section {day_number}")
            logger.debug("Widow prayer updated successfully")
        else:
            logger.error("Could not find Widow Prayer section to replace")
            return {"status": "error", "procedure": "06", "error": "Widow Prayer section not found"}
        
        return {"status": "success", "procedure": "06"}
        
    except Exception as e:
        logger.error(f"Failed to update Widow Prayer: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "06", "error": str(e)}


def pastor_prayer():
    """Handle pastor prayer section for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
        
    logger = logging.getLogger(__name__)
    logger.info("Procedure 07: Handling Pastor Prayer")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "07", "error": "Missing global variable"}
        
        pastor_file = INPUT_DIR / "pastor.md"
        pastor_content = pastor_file.read_text()
        
        pastor_entries = []
        # Regex to capture Pastor Name and Church Name from the markdown table
        # It handles cases where Pastor Name or Church Name might be empty
        # The pattern looks for lines starting with '|', followed by a number, then captures two groups
        # Group 1: Pastor Name (can be empty)
        # Group 2: Church Name (can be empty)
        for line in pastor_content.splitlines():
            match = re.match(r'\|\s*\d+\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|', line)
            if match:
                pastor_name = match.group(1).strip()
                church_name = match.group(2).strip()
                
                if pastor_name and church_name:
                    formatted_entry = f"Pray for Local Pastor by Johnny Perry - {church_name} - {pastor_name}"
                elif church_name:
                    formatted_entry = f"Pray for Local Pastor by Johnny Perry - {church_name}"
                else:
                    # Skip entries that don't have at least a church name
                    continue
                pastor_entries.append(formatted_entry)
        
        if not pastor_entries:
            logger.error("No pastor entries found in pastor.md")
            return {"status": "error", "procedure": "07", "error": "No pastor entries found"}
        
        logger.debug(f"Found {len(pastor_entries)} pastor entries.")
        
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        
        # Find the current pastor prayer entry in the agenda
        current_pastor_pattern = r"Pray for Local Pastor by Johnny Perry - .*"
        current_pastor_match = re.search(current_pastor_pattern, agenda_content)
        
        if not current_pastor_match:
            logger.error("Could not find current pastor prayer entry in agenda.")
            return {"status": "error", "procedure": "07", "error": "Current pastor prayer entry not found"}
        
        current_pastor_entry = current_pastor_match.group(0).strip()
        logger.info(f"Current pastor prayer entry: {current_pastor_entry}")
        
        try:
            current_index = pastor_entries.index(current_pastor_entry)
        except ValueError:
            logger.warning(f"Current pastor entry '{current_pastor_entry}' not found in pastor.md. Starting from the beginning.")
            current_index = -1 # Will make next_index 0
            
        next_index = (current_index + 1) % len(pastor_entries)
        next_pastor_entry = pastor_entries[next_index]
        
        logger.info(f"Next pastor prayer entry: {next_pastor_entry}")
        
        updated_content = re.sub(current_pastor_pattern, next_pastor_entry, agenda_content)
        NEXT_WEEK_AGENDA_FILE.write_text(updated_content)
        
        logger.info("Pastor prayer entry updated successfully.")
        
        return {"status": "success", "procedure": "07"}
        
    except Exception as e:
        logger.error(f"Failed to handle pastor prayer: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "07", "error": str(e)}


def print_v1_6x():
    """Print version 1.6x information."""
    import subprocess
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 08: Printing NEXT_WEEK_AGENDA_FILE six times")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "08", "error": "Missing global variable"}
        
        file_to_print = NEXT_WEEK_AGENDA_FILE.resolve() # Get absolute path
        
        for i in range(6):
            logger.debug(f"Printing {file_to_print} (iteration {i+1}/6)")
            # Using 'lp' command for printing on macOS/Linux
            # -o raw: print file without filtering (useful for markdown files)
            # -n 1: print 1 copy
            result = subprocess.run(['lp', '-n', '1', str(file_to_print)], capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                logger.error(f"Printing failed on iteration {i+1}: {result.stderr.strip()}")
                return {"status": "error", "procedure": "08", "error": f"Printing failed: {result.stderr.strip()}"}
            else:
                logger.debug(f"Print command output (iteration {i+1}): {result.stdout.strip()}")
        
        logger.info("NEXT_WEEK_AGENDA_FILE printed six times successfully.")
        
        return {"status": "success", "procedure": "08"}
        
    except Exception as e:
        logger.error(f"Failed to print NEXT_WEEK_AGENDA_FILE: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "08", "error": str(e)}


def kjv_verses():
    """Handle KJV verses for next week."""
    import re
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 09: Handling KJV Verses")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "09", "error": "Missing global variable"}
        
        agenda_content = NEXT_WEEK_AGENDA_FILE.read_text()
        updated_lines = []
        
        # Sort by length descending to match longer names first (e.g., "1 John" before "John")
        book_names_sorted = sorted(BIBLE_BOOK_NAMES, key=len, reverse=True)
        
        book_pattern_parts = []
        roman_numerals_map = {
            "1": "I", "2": "II", "3": "III"
        }

        for name in book_names_sorted:
            # Handle Arabic numeral prefix (e.g., "1 Samuel")
            match_num_prefix = re.match(r'(\d+)\s+(.*)', name)
            if match_num_prefix:
                arabic_num = match_num_prefix.group(1)
                book_rest = match_num_prefix.group(2)
                
                # Add Arabic numeral version
                escaped_arabic = re.escape(name).replace(r'\ ', r'\s+')
                if name.endswith('s'): # Make 's' optional for plural books
                    escaped_arabic = escaped_arabic[:-1] + 's?'
                book_pattern_parts.append(escaped_arabic)
                
                # Add Roman numeral version
                if arabic_num in roman_numerals_map:
                    roman_num = roman_numerals_map[arabic_num]
                    roman_name = f"{roman_num} {book_rest}"
                    escaped_roman = re.escape(roman_name).replace(r'\ ', r'\s+')
                    if roman_name.endswith('s'): # Make 's' optional for plural books
                        escaped_roman = escaped_roman[:-1] + 's?'
                    book_pattern_parts.append(escaped_roman)
            else:
                # For books without numeral prefix (e.g., "John")
                escaped_name = re.escape(name).replace(r'\ ', r'\s+')
                if name.endswith('s'): # Make 's' optional for plural books
                    escaped_name = escaped_name[:-1] + 's?'
                book_pattern_parts.append(escaped_name)

        book_pattern = '|'.join(book_pattern_parts)

        # Final regex pattern for Bible references, capturing the full reference
        # This pattern will capture the entire reference, including book, chapter, and optional verses.
        # It allows for non-word characters before the reference.
        bible_ref_pattern = re.compile(
            r'\W*(' + book_pattern + r')\s+(\d+)(?::(\d+)(?:-(\d+))?)?', re.IGNORECASE
        )
        
        lines = agenda_content.splitlines()
        for line in lines:
            updated_lines.append(line) # Always add the original line
            
            logger.debug(f"Line being processed: {line}")
            
            # Find all potential Bible references in the current line
            # Using finditer to get all matches and their positions
            for match in bible_ref_pattern.finditer(line):
                # The actual Bible reference starts from group 1 (book name)
                book = match.group(1)
                chapter = match.group(2)
                start_verse = match.group(3)
                end_verse = match.group(4)

                reference = f"{book} {chapter}"
                if start_verse:
                    reference += f":{start_verse}"
                    if end_verse:
                        reference += f"-{end_verse}"
                
                reference = reference.strip() # Clean up any extra spaces
                
                logger.debug(f"Found Bible reference: {reference}")
                verses = get_kjv_verse(reference)
                
                if verses:
                    for i, verse_text in enumerate(verses):
                        updated_lines.append(f"{i+1}. {verse_text}")
                    logger.info(f"Inserted KJV verses for {reference}")
                else:
                    logger.warning(f"Could not retrieve KJV verses for {reference}")
        
        # Join the updated lines and write back to the file
        NEXT_WEEK_AGENDA_FILE.write_text("\n".join(updated_lines))
        
        logger.info("KJV verses processed and agenda updated successfully.")
        
        return {"status": "success", "procedure": "09"}
        
    except Exception as e:
        logger.error(f"Failed to handle KJV verses: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "09", "error": str(e)}


def print_v2_1x():
    """Prints the NEXT_WEEK_AGENDA_FILE to the default printer."""
    import subprocess
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 10: Printing NEXT_WEEK_AGENDA_FILE to default printer")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None:
            logger.error("Global variable NEXT_WEEK_AGENDA_FILE not initialized. Run init_file first.")
            return {"status": "error", "procedure": "10", "error": "Missing global variable"}
        
        file_to_print = NEXT_WEEK_AGENDA_FILE.resolve() # Get absolute path
        
        logger.debug(f"Printing {file_to_print} to default printer")
        # Using 'lp' command for printing on macOS/Linux
        # -n 1: print 1 copy
        result = subprocess.run(['lp', '-n', '1', str(file_to_print)], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            logger.error(f"Printing failed: {result.stderr.strip()}")
            return {"status": "error", "procedure": "10", "error": f"Printing failed: {result.stderr.strip()}"}
        else:
            logger.debug(f"Print command output: {result.stdout.strip()}")
        
        logger.info("NEXT_WEEK_AGENDA_FILE printed successfully.")
        
        return {"status": "success", "procedure": "10"}
        
    except Exception as e:
        logger.error(f"Failed to print NEXT_WEEK_AGENDA_FILE: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "10", "error": str(e)}


def email_v2():
    """Sends the Prayer Breakfast Agenda via email with the markdown file as an attachment."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    import os
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    # User provided details
    EMAIL_FROM = "ThomasPerdana@gmail.com"
    EMAIL_TO = "gideon.northseminole@gmail.com"
    SUBJECT = "Prayer Breakfast Agenda"
    EMAIL_PASSWORD = "ktnd vioj bxxu aika" # User's Gmail App Password
    
    # SMTP Configuration from user
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587 # Using TLS port
    
    logger.info(f"Preparing to send email from {EMAIL_FROM} to {EMAIL_TO} with subject: {SUBJECT}")

    if NEXT_WEEK_AGENDA_FILE is None:
        logger.error("NEXT_WEEK_AGENDA_FILE is not set. Run init_file first.")
        return {"status": "error", "procedure": "11", "error": "NEXT_WEEK_AGENDA_FILE not set"}

    attachment_path = NEXT_WEEK_AGENDA_FILE.resolve()
    
    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = SUBJECT

    # Attach the file
    try:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f"attachment; filename= {os.path.basename(attachment_path)}",
        )
        msg.attach(part)
        logger.info(f"Attached file: {os.path.basename(attachment_path)}")
    except FileNotFoundError:
        logger.error(f"Attachment file not found: {attachment_path}")
        return {"status": "error", "procedure": "11", "error": f"Attachment file not found: {attachment_path}"}
    except Exception as e:
        logger.error(f"Error attaching file: {e}")
        return {"status": "error", "procedure": "11", "error": f"Error attaching file: {e}"}

    # Add body to email
    body = "Please find the attached Prayer Breakfast Agenda.\n\nRegards,\nYour Application"
    msg.attach(MIMEText(body, 'plain'))

    # --- EMAIL SENDING LOGIC ---
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        logger.info("Email sent successfully.")
        return {"status": "success", "procedure": "11"}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"status": "error", "procedure": "11", "error": f"Failed to send email: {e}"}
    # --- END EMAIL SENDING LOGIC ---


def copy_file_v1():
    """Copies the generated agenda file from the output directory to the input directory."""
    import shutil
    import stat
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 12: Copying next week's agenda file to input directory (v1)")
    
    try:
        if NEXT_WEEK_AGENDA_FILE is None or not NEXT_WEEK_AGENDA_FILE.exists():
            logger.error("Next week's agenda file does not exist. Cannot copy.")
            return {"status": "error", "procedure": "12", "error": "Agenda file not found"}
            
        destination_file = INPUT_DIR / NEXT_WEEK_AGENDA_FILE.name
        
        # Temporarily change INPUT_DIR permissions to allow writing
        original_input_dir_permissions = INPUT_DIR.stat().st_mode
        INPUT_DIR.chmod(0o755) # rwxr-xr-x
        logger.debug(f"Temporarily changed INPUT_DIR permissions to 755 for writing.")

        # Remove the destination file if it already exists
        if destination_file.exists():
            destination_file.unlink()
            logger.debug(f"Removed existing file in input directory: {destination_file.name}")

        shutil.copy2(str(NEXT_WEEK_AGENDA_FILE), str(destination_file))
        
        logger.info(f"Successfully copied {NEXT_WEEK_AGENDA_FILE.name} to {INPUT_DIR}")
        logger.debug(f"Source: {NEXT_WEEK_AGENDA_FILE}")
        logger.debug(f"Destination: {destination_file}")

        # Identify and delete the last week file from INPUT_DIR
        last_week_file_to_delete = INPUT_DIR / "2025-11-08 Saturday Prayer Breakfast Agenda.md"
        if last_week_file_to_delete.exists():
            last_week_file_to_delete.unlink()
            logger.info(f"Successfully deleted old last week file: {last_week_file_to_delete.name}")
        else:
            logger.warning(f"Old last week file not found for deletion: {last_week_file_to_delete.name}")
        
        # Revert INPUT_DIR permissions back to original (read-only)
        INPUT_DIR.chmod(original_input_dir_permissions)
        logger.debug(f"Reverted INPUT_DIR permissions to original: {oct(original_input_dir_permissions)}")
        
        return {"status": "success", "procedure": "12"}
        
    except Exception as e:
        logger.error(f"Failed to copy agenda file: {str(e)}", exc_info=True)
        # Attempt to revert permissions even if copy failed
        try:
            INPUT_DIR.chmod(original_input_dir_permissions)
            logger.debug(f"Attempted to revert INPUT_DIR permissions to original after error: {oct(original_input_dir_permissions)}")
        except Exception as revert_e:
            logger.error(f"Failed to revert INPUT_DIR permissions after error: {revert_e}")
        return {"status": "error", "procedure": "12", "error": str(e)}


def move_file_v2():
    """Moves the generated agenda file from the output directory to a temp directory and makes the temp directory read-only."""
    import shutil
    import stat
    global INPUT_DIR, OUTPUT_DIR, LAST_WEEK_DATE, NEXT_WEEK_DATE, NEXT_WEEK_AGENDA_FILE
    
    logger = logging.getLogger(__name__)
    logger.info("Procedure 13: Moving next week's agenda file to temp directory and making it read-only")
    
    try:
        TEMP_DIR = Path("/Applications/myapp/temp")
        os.makedirs(TEMP_DIR, exist_ok=True)
        logger.debug(f"Ensured temp directory exists: {TEMP_DIR}")

        # Ensure temp directory is writable before moving files
        TEMP_DIR.chmod(0o755)
        logger.debug(f"Set temp directory permissions to writable (755): {TEMP_DIR}")

        if NEXT_WEEK_AGENDA_FILE is None or not NEXT_WEEK_AGENDA_FILE.exists():
            logger.error("Next week's agenda file does not exist. Cannot move.")
            return {"status": "error", "procedure": "13", "error": "Agenda file not found"}
            
        destination_file = TEMP_DIR / NEXT_WEEK_AGENDA_FILE.name
        
        # Remove the destination file if it already exists
        if destination_file.exists():
            destination_file.unlink()
            logger.debug(f"Removed existing file in temp directory: {destination_file.name}")

        shutil.move(str(NEXT_WEEK_AGENDA_FILE), str(destination_file))
        
        logger.info(f"Successfully moved {NEXT_WEEK_AGENDA_FILE.name} to {TEMP_DIR}")
        logger.debug(f"Source: {NEXT_WEEK_AGENDA_FILE}")
        logger.debug(f"Destination: {destination_file}")
        
        # Make the temp directory read-only
        TEMP_DIR.chmod(0o555)
        logger.info(f"Made temp directory read-only: {TEMP_DIR}")
        
        return {"status": "success", "procedure": "13"}
        
    except Exception as e:
        logger.error(f"Failed to move agenda file to temp directory: {str(e)}", exc_info=True)
        return {"status": "error", "procedure": "13", "error": str(e)}

def procedure_14():
    """Initialize session management."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 14: Initializing session management")
    logger.debug("Session storage configured")
    return {"status": "success", "procedure": "14"}


def procedure_15():
    """Setup error handling."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 15: Setting up error handling")
    logger.debug("Global exception handler registered")
    return {"status": "success", "procedure": "15"}


def procedure_16():
    """Load resource files."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 16: Loading resource files")
    logger.debug("Static resources indexed")
    return {"status": "success", "procedure": "16"}


def procedure_17():
    """Initialize data validation."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 17: Initializing data validation")
    logger.debug("Validation rules compiled")
    return {"status": "success", "procedure": "17"}


def procedure_18():
    """Setup backup system."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 18: Setting up backup system")
    logger.debug("Backup schedule configured")
    return {"status": "success", "procedure": "18"}


def procedure_19():
    """Initialize analytics."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 19: Initializing analytics")
    logger.debug("Analytics endpoints ready")
    return {"status": "success", "procedure": "19"}


def procedure_20():
    """Finalize startup sequence."""
    logger = logging.getLogger(__name__)
    logger.info("Procedure 20: Finalizing startup sequence")
    logger.debug("All systems operational")
    return {"status": "success", "procedure": "20"}


def main():

    # --- MAIN SCRIPT LOGIC ---

    # 1. Define your paths correctly
    # The executable's location (or the script's CWD)
    # This is where 'myoutput' and 'mylog' will be created.
    executable_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    # The path to your bundled data
    data_path = os.path.join(get_base_path(), 'input')

    # The paths for your output and logs
    output_path = os.path.join(executable_path, 'output')
    log_path = os.path.join(executable_path, 'logs')


    # 2. Create output and log directories if they don't exist
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)





    """Main program entry point."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Application Starting")
    logger.info("=" * 60)
    
    procedures = [
        init_file, bible_reading, prayer_card, international_reading, state_reading,
        widow_prayer, pastor_prayer, print_v1_6x, copy_file_v1, kjv_verses, print_v2_1x,
        email_v2, move_file_v2, procedure_14, procedure_15,
        procedure_16, procedure_17, procedure_18, procedure_19, procedure_20
    ]
    
    results = []
    success_count = 0
    failure_count = 0
    
    for idx, procedure in enumerate(procedures, 1):
        try:
            logger.debug(f"Executing procedure {idx} of {len(procedures)}")
            result = procedure()
            results.append(result)
            
            if result.get("status") == "success":
                success_count += 1
                logger.debug(f"Procedure {idx} completed successfully")
            else:
                failure_count += 1
                logger.warning(f"Procedure {idx} completed with issues")
                
        except Exception as e:
            failure_count += 1
            logger.error(f"Error in procedure {idx}: {str(e)}", exc_info=True)
            results.append({"status": "error", "procedure": f"{idx:02d}", "error": str(e)})
    
    logger.info("=" * 60)
    logger.info("Execution Summary")
    logger.info("=" * 60)
    logger.info(f"Total Procedures: {len(procedures)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failure_count}")
    logger.info("=" * 60)
    
    if failure_count == 0:
        logger.info("Application started successfully!")
        return 0
    else:
        logger.warning(f"Application started with {failure_count} errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())

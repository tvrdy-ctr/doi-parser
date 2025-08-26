from colorama import Fore, Style, init
from constants import (
    organization_to_ror_lookup,
    API_URL_Lookup,
    ROR_CLIENT_ID
)
import json
import logging
import requests
from confirmed_matches import (
    confirmed_matches,
    rejection_list
)
import sys

init(autoreset=True)

# Prompts users to manually provide ROR ID for an organization if API search was not successful and didn't find a good match
def ror_manual_search(corporate_creator):
    while True:
        ror_id = input(f"\nPlease enter the {Fore.CYAN}ROR ID {Style.RESET_ALL}(either the full URL or just the ID), press Enter to skip, or type 'exit' to cancel: ").strip()
        
        if ror_id.lower() == 'exit':
            return None, None, None, None

        if ror_id and not ror_id.startswith("https://ror.org/"):
            ror_id = "https://ror.org/" + ror_id

        if ror_id:
            ror_name = input(f"Please enter the {Fore.CYAN}ROR Display Name{Style.RESET_ALL} for your organization or type 'exit' to cancel: ").strip()
            if ror_name.lower() == 'exit':
                return None, None, None, None
            user_input_correct = input(f"You have entered the ROR ID {Fore.GREEN}{ror_id}{Style.RESET_ALL} and the ROR Display Name {Fore.GREEN}{ror_name}{Style.RESET_ALL}. Is this correct? (Y/n): ").strip().upper()
            if user_input_correct == 'N':
                retry_input = input(f"\nWould you like to retry entry? (y/n): ").strip().upper()
                if retry_input == 'N':
                    return None, None, None, None
                else:
                    continue
        else:
            # Blank ROR ID input
            ror_id = ""
            ror_name = input(f"Please enter the {Fore.CYAN}Preferred Display Name{Style.RESET_ALL} for your organization or type 'exit' to cancel: ").strip()
            if ror_name.lower() == 'exit':
                return None, None, None, None
            user_input_correct_no_ror = input(f"You have entered {Fore.RED}NO ROR ID{Style.RESET_ALL} and the Preferred Display Name {Fore.GREEN}{ror_name}{Style.RESET_ALL}. Is this correct? (Y/n): ").strip().upper()
            if user_input_correct_no_ror == 'N':
                retry_input = input(f"\nWould you like to retry entry? (y/n): ").strip().upper()
                if retry_input == 'N':
                    return None, None, None, None
                else:
                    continue

        # Ask about optional affiliation
        add_affiliation = input("Would you like to add an affiliation ROR ID and Name? (Y/N): ").strip().lower()
        if add_affiliation == 'y':
            affiliation_ror_id = input("Enter Affiliation ROR ID: ").strip()
            if not affiliation_ror_id.startswith("https://ror.org/"):
                affiliation_ror_id = "https://ror.org/" + affiliation_ror_id
            affiliation_ror_name = input("Enter Affiliation ROR Name: ").strip()
        else:
            affiliation_ror_id = ""
            affiliation_ror_name = ""

        confirmed_matches[corporate_creator] = {
            'ror_id': ror_id,
            'ror_name': ror_name,
            'affiliation_ror_id': affiliation_ror_id,
            'affiliation_ror_name': affiliation_ror_name
        }

        return ror_id, ror_name, affiliation_ror_id, affiliation_ror_name

# Prompts users to manually provide ROR ID information if the API isn't working
def ror_manual_addition(corporate_creator):
    while True:
        def ror_manual_addition(corporate_creator):
            print(f"\n{Fore.YELLOW}No valid ROR match found for: {Fore.CYAN}{corporate_creator}{Style.RESET_ALL}")
            user_choice = input("Would you like to manually enter a ROR ID and Name for this organization? (Y/N): ").strip().lower()

            if user_choice != 'y':
                rejection_list.append(corporate_creator)
                return None, None, None, None

            ror_id = input("Enter ROR ID (e.g. https://ror.org/012345678): ").strip()
            ror_name = input("Enter ROR Name: ").strip()

            # Optional: Ask for affiliation ROR details
            add_affiliation = input("Would you like to add an {Fore.YELLOW}*affiliation*{Style.RESET_ALL} ROR ID and Name? (Y/N): ").strip().lower()
            if add_affiliation == 'y':
                affiliation_ror_id = input("Enter Affiliation ROR ID: ").strip()
                affiliation_ror_name = input("Enter Affiliation ROR Name: ").strip()
            else:
                affiliation_ror_id = ""
                affiliation_ror_name = ""

            confirmed_matches[corporate_creator] = {
                'ror_id': ror_id,
                'ror_name': ror_name,
                'affiliation_ror_id': affiliation_ror_id,
                'affiliation_ror_name': affiliation_ror_name
            }

            return ror_id, ror_name, affiliation_ror_id, affiliation_ror_name

        
# Prompts user to verify the match the ROR API provided and saves the confirmed match 
def verify_match(corporate_creator, ror_id, ror_name):
    while True:
        user_input = input(f"\n\nROR would like to match {Fore.GREEN}'{corporate_creator}{Style.RESET_ALL}' to {Fore.CYAN}'{ror_name}' (ROR ID: {ror_id}){Style.RESET_ALL}. Is this a correct match? (y/N): ").strip().upper()
        if user_input == 'N':
            rejection_list.append(corporate_creator)
            return False
        if user_input == 'Y':
            confirmed_matches[corporate_creator] = {"ror_id": ror_id, "ror_name": ror_name}
            return True
        else:
            print(f"{Fore.RED}Invalid input.{Style.RESET_ALL} Please enter 'Y' or 'N'.")
    

def get_ror_info(corporate_creator, skip_ror_api=False):
    try:
        # check if we already rejected this corporate creator in the same process
        if corporate_creator in rejection_list:
            print(f"Skipping corporate creator query for {Fore.RED}{corporate_creator}\n")
            return None, None, None, None

        # Check if the corporate creator exists in confirmed matches
        if corporate_creator in confirmed_matches and confirmed_matches[corporate_creator]["ror_name"]:
            logging.info(f'Using previously confirmed match for {corporate_creator}.')
            ror_info = confirmed_matches[corporate_creator]
            return (
                ror_info['ror_id'],
                ror_info['ror_name'],
                ror_info.get('affiliation_ror_id', '').strip(),
                ror_info.get('affiliation_ror_name', '').strip()
            )

        
        # If skipping ROR API checking, return None if not found
        if skip_ror_api:
            logging.info(f"Skipping ROR API lookup for {corporate_creator}. No match found in confirmed_matches.")
            return None, None, None, None
        
        # Check if the corporate creator exists in the dictionary
        if corporate_creator in organization_to_ror_lookup:
            logging.info(f"Picking {corporate_creator} from organization_to_ror_lookup")
            ror_id = organization_to_ror_lookup[corporate_creator]
            
            # Clean up the name for display
            corporate_creator = corporate_creator.replace("United States. Department of Transportation. ", "")
            ror_name_unclean = corporate_creator
            ror_name_step1 = ror_name_unclean.replace("United States. ", "") 
            ror_name = ror_name_step1.replace("Department of Transportation. ", "")
            
            # Define these as empty strings if not applicable
            affiliation_ror_id = ""
            affiliation_ror_name = ""
            
            return ror_id, ror_name, affiliation_ror_id, affiliation_ror_name

        
        # Query the ROR API
        API_URL = API_URL_Lookup["API_URL"]
        logging.info(f"Preparing ORG ID Request for {corporate_creator}")
        
        headers = {"Client-Id": ROR_CLIENT_ID}
        response = requests.get(API_URL, headers=headers, params={'affiliation': corporate_creator})
        logging.info(f"Org ID Response Status: {response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"API request failed for '{corporate_creator}' with status code {response.status_code}.")
            return ror_manual_addition(corporate_creator)
        
        ror_data = response.json()
        logging.debug(f"API Response is: {ror_data}")
        
        if not ror_data.get('items'):
            logging.error(f"Malformed ROR response for {corporate_creator}")
            return ror_manual_addition(corporate_creator)
        
        items_list = ror_data['items']
        closest_match = next((item for item in items_list if item.get('chosen', False)), items_list[0])
        
        logging.debug(f"My Closest Match Is: {closest_match}")
        ror_id = closest_match["organization"]['id']
        
        for name_entry in closest_match['organization'].get('names', []):
            if 'ror_display' in name_entry.get('types', []):
                ror_name = name_entry.get('value')
                logging.debug(f"Taking ror_display as the name {ror_name}")
                
                if verify_match(corporate_creator, ror_id, ror_name):
                    confirmed_matches[corporate_creator] = {'ror_id': ror_id, 'ror_name': ror_name}
                    return ror_id, ror_name, "", ""
                
                return ror_manual_search(corporate_creator)

    except Exception as e:
        logging.error(f"Error fetching ROR data for '{corporate_creator}': {e}")
        sys.exit(1)

    return None, None, None, None



def delete_unwanted(json_obj, key):
    if key in json_obj:
        del json_obj[key]
        
        
def doi_publish(url, obj, headers):
    payload = json.dumps(obj)
    if 'doi' in obj['data']['attributes']:
        doi = obj['data']['attributes']['doi']
        return requests.put(url + '/' + doi, data=payload, headers=headers)
    else:
        return requests.post(url, data=payload, headers=headers)
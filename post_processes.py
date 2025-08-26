from constants import (
    collections_to_doi_lookup,
    series_to_doi_lookup,
    resource_type_lookup,
    language_dict,
    iana_mime_type_lookup
)

import datetime as dt
import logging
import os

from orcids import (
    orcids
)
import pandas as pd

from utils import (
    get_ror_info,
    delete_unwanted
)

# logging.basicConfig(filename="process.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#this function removes unneeded columns from the CSV: "Main Document URL", "Supporting Documents URLs", "sm:Publisher", "Geographical Coverage", "sm:Rights Statement"
def delete_unwanted_columns(json_list):
    for json_obj in (json_list):
        delete_unwanted(json_obj, "Main Document URL")
        delete_unwanted(json_obj, "Supporting Documents URLs")
        delete_unwanted(json_obj, "sm:Publisher")
        delete_unwanted(json_obj, "sm:Geographical Coverage")
        delete_unwanted(json_obj, "Primary URL")
        delete_unwanted(json_obj, "Supporting Files")
        delete_unwanted(json_obj, "Alternate URL(s)")
        delete_unwanted(json_obj, "Geographical Coverage")
        delete_unwanted(json_obj, "Classification")
        delete_unwanted(json_obj, "Subject Keywords")
        delete_unwanted(json_obj, "Publication Year")
        delete_unwanted(json_obj, "Publication Month")
        delete_unwanted(json_obj, "Publication Day")
        delete_unwanted(json_obj, "Distribution Hold Start Date")
        delete_unwanted(json_obj, "Distribution Hold End Date")
        delete_unwanted(json_obj, "Supplier")
        delete_unwanted(json_obj, "Staff Notes")
        delete_unwanted(json_obj, "Status")
        delete_unwanted(json_obj, "Status Comment")
        delete_unwanted(json_obj, "Modified By")
        delete_unwanted(json_obj, "Date Created")
        delete_unwanted(json_obj, "Created By")
        delete_unwanted(json_obj, "Comment Date")
        delete_unwanted(json_obj, "Comment By")
        delete_unwanted(json_obj, "Is Version of")
        delete_unwanted(json_obj, "Contains")
        delete_unwanted(json_obj, "Is Format Of")
        delete_unwanted(json_obj, "Requires")
        delete_unwanted(json_obj, "References")
        delete_unwanted(json_obj, "Preceding Entry")
        delete_unwanted(json_obj, "TAG for Ingest")
        delete_unwanted(json_obj, "Collection_PID")
        delete_unwanted(json_obj, "Key Type")
        delete_unwanted(json_obj, "Key Value")
        delete_unwanted(json_obj, "DOCID")
    return json_list

#this function matches "Workroom ID" to Alternateidentifier
def workroom_id(json_list):
    for index, json_obj in enumerate(json_list):
        if "Workroom ID" in json_obj or "Workroom_ID" in json_obj:
            accession_number = json_obj.pop("Workroom ID", json_obj.pop("Workroom_ID", None))
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": accession_number, 
                "alternateIdentifierType": "DOT ROSA P Accession Number"
            })
        else:
            logging.info(f"Workroom ID not found for row {index +1}.")
    return json_list

#this function matches "ROSAP ID" to Alternateidentifier
def rosap_id(json_list):
    for index, json_obj in enumerate(json_list):
        if "ROSAP ID" in json_obj or "ROSAP_ID" in json_obj or "ROSA P_ID" in json_obj:
            swat_id = json_obj.pop("ROSAP ID", json_obj.pop("ROSAP_ID", json_obj.pop("ROSA P_ID", None)))
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": swat_id, 
                "alternateIdentifierType": "CDC SWAT Identifier"
                })
        else:
            logging.info(f"ROSAP ID not found for row {index + 1}.")
    return json_list
    
#this function matches "ISSN" to Alternateidentifier
def issn_number(json_list):
    for json_obj in json_list:
        if "ISSN" in json_obj:
            issn = json_obj.pop("ISSN").strip()
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": issn,
                "alternateIdentifierType": "ISSN"
            })
    return json_list
    
#this function matches "TRIS" to Alternateidentifier
def tris(json_list):
    for json_obj in json_list:
        if "TRIS" in json_obj:
            tris = json_obj.pop("TRIS").strip()
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": tris,
                "alternateIdentifierType": "Transportation Research Information Services (TRIS) Database Accession Number"
            })
    return json_list
            
def oclc(json_list):
    for json_obj in json_list:
        if "OCLC" in json_obj:
            oclc = json_obj.pop("OCLC").strip()
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": oclc,
                "alternateIdentifierType": "OCLC Number"
            })
    return json_list
            
def isbn(json_list):
    for json_obj in json_list:
        if "ISBN" in json_list:
            isbn = json_obj.pop("ISBN").strip()
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": isbn,
                "alternateIdentifierType": "ISBN"
            })
    return json_list
    
#this function matches "ROSAP URLs" to url
def rosap_url(json_list):
    for index, json_obj in enumerate(json_list):
        rosap_key = None
        for candidate_key in ("ROSAP URLs", "ROSAP_URL", "ROSAP URL", "ROSAP_URLs", "ROSAP URLS", "ROSA P URL", "ROSA P URLS", "ROSA P_URL"):
            if candidate_key in json_obj:
                rosap_key = candidate_key
                break
        if rosap_key is not None:
            url = json_obj.pop(rosap_key)
            json_obj["url"] = url
            if "https://highways.dot.gov/" in url:
                json_obj.setdefault("contributors", []).extend([
                    {
                        "name": "Federal Highway Administration", 
                        "nameType": "Organizational", 
                        "contributorType": "HostingInstitution", 
                        "lang": "en", 
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "https://ror.org/0473rr271", 
                                "nameIdentifierScheme": "ROR", 
                                "schemeUri": "https://ror.org/"
                            }
                        ]
                    },
                    {
                        "name": "Federal Highway Administration", 
                        "nameType": "Organizational", 
                        "contributorType": "Distributor", 
                        "lang": "en", 
                        "nameIdentifiers": [
                            {
                                "nameIdentifier": "https://ror.org/0473rr271", 
                                "nameIdentifierScheme": "ROR", 
                                "schemeUri": "https://ror.org/"
                            }
                        ]
                    }
                ])
            elif "https://cms.fhwa.dot.gov/" in url:
                json_obj.setdefault("contributors", []).extend([
                    {
                        "name": "Federal Highway Administration", 
                        "nameType": "Organizational", 
                        "contributorType": "HostingInstitution", 
                        "lang": "en", 
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/0473rr271", 
                            "nameIdentifierScheme": "ROR", 
                            "schemeUri": "https://ror.org/"}
                        ]
                    },
                    {
                    "name": "Federal Highway Administration", 
                        "nameType": "Organizational", 
                        "contributorType": "Distributor", 
                        "lang": "en", 
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/0473rr271", 
                            "nameIdentifierScheme": "ROR", 
                            "schemeUri": "https://ror.org/"}
                        ]
                    }
                ])
            elif "geodata.bts.gov" in url:
                json_obj.setdefault("contributors", []).append([
                    {
                        "name": "Bureau of Transportation Statistics",
                        "nameType": "Organizational",
                        "contributorType": "HostingInstitution",
                        "lang": "en",
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/05xfdey77",
                            "nameIdentifierScheme": "ROR",
                            "schemeUri": "https://ror.org/"}
                        ]
                    },
                    {
                        "name": "Bureau of Transportation Statistics",
                        "nameType": "Organizational",
                        "contributorType": "Distributor",
                        "lang": "en",
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/05xfdey77",
                            "nameIdentifierScheme": "ROR",
                            "schemeUri": "https://ror.org/"}
                        ]
                    }
                ])
            elif "https://services.arcgis.com" in url:
                json_obj.setdefault("contributors", []).append([
                    {
                        "name": "Bureau of Transportation Statistics",
                        "nameType": "Organizational",
                        "contributorType": "HostingInstitution",
                        "lang": "en",
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/05xfdey77",
                            "nameIdentifierScheme": "ROR",
                            "schemeUri": "https://ror.org/"}
                        ]
                    },
                    {
                        "name": "Bureau of Transportation Statistics",
                        "nameType": "Organizational",
                        "contributorType": "Distributor",
                        "lang": "en",
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/05xfdey77",
                            "nameIdentifierScheme": "ROR",
                            "schemeUri": "https://ror.org/"}
                        ]
                    }
                ])
            elif "https://rosap.ntl.bts.gov/" in url:
                json_obj.setdefault("contributors", []).extend([
                    {
                        "name": "National Transportation Library", 
                        "nameType": "Organizational", 
                        "contributorType": "HostingInstitution", 
                        "lang": "en", 
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/00snbrd52", 
                            "nameIdentifierScheme": "ROR", 
                            "schemeUri": "https://ror.org/"}
                        ]
                    },
                    {
                        "name": "National Transportation Library", 
                        "nameType": "Organizational", 
                        "contributorType": "Distributor", 
                        "lang": "en", 
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/00snbrd52", 
                            "nameIdentifierScheme": "ROR", 
                            "schemeUri": "https://ror.org/"}
                        ]
                    }
                ])
            elif "data.transportation.gov" in url:
                json_obj.setdefault("contributors", []).append([
                    {
                        "name": "United States Department of Transportation",
                        "nameType": "Organizational",
                        "contributorType": "HostingInstitution",
                        "lang": "en",
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/02xfw2e90",
                            "nameIdentifierScheme": "ROR",
                            "schemeUri": "https://ror.org/"}
                        ]
                    },
                    {
                        "name": "United States Department of Transportation",
                        "nameType": "Organizational",
                        "contributorType": "Distributor",
                        "lang": "en",
                        "nameIdentifiers": [
                            {"nameIdentifier": "https://ror.org/02xfw2e90",
                            "nameIdentifierScheme": "ROR",
                            "schemeUri": "https://ror.org/"}
                        ]
                    }
                ])
            else:
                logging.warn(f"ROSAP URLs contributor not mapped for {index + 1}. URL: ${url}")
        else:
            logging.info(f"ROSAP URL not found for row {index + 1}.")
    return json_list

#this function matches "sm:Collection" to RelatedIdentifier
def sm_Collection(json_list):
    for index, json_obj in enumerate(json_list):
        if "sm:Collection" in json_obj or "Collection(s) in json_obj":
            collections = json_obj.pop("sm:Collection", json_obj.pop("Collection(s)", ""))
            collections = collections.split(";") if collections else ["US Transportation Collection"]
            for collection in collections:
                collection = collection.strip()
                if collection in collections_to_doi_lookup:
                    #Create a new DOI-related entry
                    doi_entry_collection = {
                        "relatedIdentifier": collections_to_doi_lookup[collection],
                        "relatedIdentifierType": "DOI",
                        "relationType": "IsPartOf",
                        "resourceTypeGeneral": "Collection"
                    }
                    #Initialize "related_identifiers" if not already present
                    json_obj.setdefault("relatedIdentifiers", []).append(doi_entry_collection)
                else:
                    logging.warn(f"Collection {collection} not found in lookup for row {index + 1}.")
        else:
            logging.info(f"sm:Collection not found for row {index + 1}.")
    return json_list


def handle_draft_vs_publish(json_list):
    for i, json_obj in enumerate(json_list):
        if json_obj.get("sm:Digital Object Identifier") and json_obj['sm:Digital Object Identifier'].strip():
            sm_digital_object_identifier(json_obj)
            json_obj['state'] = "update"
        elif json_obj.get("Digital Object Identifier") and json_obj['Digital Object Identifier'].strip():
            sm_digital_object_identifier(json_obj)
            json_obj['state'] = "update"
        else:
            logging.info(f"Setting to draft state for row {i}")
            draft_state(json_obj)
            json_obj['state'] = "draft"
    return json_list

#this function matches "sm:Digital Object Identifier" to doi, prefix and id
def sm_digital_object_identifier(json_obj):
    doi = json_obj.pop("sm:Digital Object Identifier", json_obj.pop("Digital Object Identifier", None))
    doi_identifier = doi.replace("https://doi.org/","").strip()
    json_obj["doi"]= doi_identifier

    prefix, suffix = doi_identifier.split('/', 2)
    json_obj["prefix"] = prefix
    json_obj["event"]= "publish"

#this function registers the DOI and the metadata in the "draft" state. This state functions much like a reserve. The attribute "prefix", without the attribute "doi", triggers suffix auto-generation.
def draft_state(json_obj):
    json_obj['prefix'] = "10.21949" # TODO: redo config.txt to something better !

            
#this function matches "Title" to titles
def title(json_list):
    logging.debug("Running title function")
    for json_obj in json_list:
        logging.debug(f"Processing object: {json_obj}")
        if "Title" in json_obj:
            title = json_obj.pop("Title")
            json_obj.setdefault("titles", []).append({
                "title": title,
                "lang": "en"
            })
    return json_list

#this function matches "Alternative Title" to title and title type
def alt_title(json_list):
    for json_obj in (json_list):
        if "Alternative Title" in json_obj or "Alternate Title" in json_obj:
            alt_title = json_obj.pop("Alternative Title", json_obj.pop("Alternate Title", None))
            json_obj.setdefault("titles", []).append({
                "title": alt_title, 
                "titleType": "AlternativeTitle", 
                "lang": "en"
                })
    return json_list
        
#this function matches "Published Date" to Publication Year, Date, and dateType
def publication_date(json_list):
    for index, json_obj in enumerate(json_list):
        date = json_obj.pop("Published Date", json_obj.pop("Publication Date", ""))
        json_obj.setdefault("dates", []).append({"date": date, "dateType": "Issued"})
        published_year = date[:4]
        if published_year.isnumeric():
            json_obj["publicationYear"] = int(published_year)
        else:
            logging.warning(f"Bad year for {index + 1} == {published_year} from date {date}")
        
    return json_list

def copyright_date(json_list):
    for index, json_obj in enumerate(json_list):
        if "Copyright Date" in json_obj:
            copywriteDate = json_obj.pop("Copyright Date").strip()
            json_obj.setdefault("dates", []).append({
                "date": copywriteDate, 
                "dateType": "Copyrighted"
                })
            logging.info(f"Copyright date mapped for row {index +1}.")
    return json_list

def date_captured(json_list):
    for index, json_obj in enumerate(json_list):
        if "Date Captured" in json_obj:
            capturedDate = json_obj.pop("Date Captured").strip()
            capturedDate = capturedDate.split(" ")[0]
            json_obj.setdefault("dates", []).append({
                "date": capturedDate,
                "dateType": "Submitted",
                "dateInformation": "Date cataloging record was first created in NTL cataloging system."
            })
        else:
            logging.info(f"No Date Captured for row {index +1}.")
    return json_list        

def modified(json_list):
    for json_obj in json_list:
        if "Date Modified" in json_obj:
            updated = json_obj.pop("Date Modified").strip()  # Ensure no leading/trailing whitespace
            updated = updated.split("T")[0] if "T" in updated else updated.split(" ")[0]  # Extract date only
            
            # Ensure "dates" exists, and append the new date
            if "dates" not in json_obj:
                json_obj["dates"] = []  # Create list if it doesn't exist

            json_obj["dates"].append({
                "date": updated,
                "dateType": "Updated",
                "dateInformation": "Date cataloging record was last modified by NTL staff."
            })    
    return json_list

def date_created(json_list):
    for json_obj in json_list:
        state = json_obj['state']
        if state == "draft":
            json_obj.setdefault("dates", []).append({
                "date": dt.datetime.today().strftime("%Y-%m-%d"),
                "dateType": "Created",
                "dateInformation": "Date DOI and record was created by NTL staff."
            })  
    return json_list
        

#this function matches "sm:Format" to ResourceType and resourceTypeGeneral
def resource_type(json_list):
    for index, json_obj in enumerate(json_list):
            if "sm:Format" and "sm:Resource Type" in json_obj or "Format" and "Resource Type" in json_obj or "Format (NTL)" and "Resource Type (NTL)" in json_obj:
                format_type = json_obj.pop("sm:Format", json_obj.pop("Format", json_obj.pop("Format (NTL)","")))
                resource_type = json_obj.get("sm:Resource Type", json_obj.get("Resource Type", ""))
                resource_type_general = json_obj.pop("sm:Resource Type", json_obj.pop("Resource Type", json_obj.pop("Resource Type (NTL)","")))
                if resource_type_general in resource_type_lookup:
                    resource_type_general = resource_type_general.strip()
                    resource_type = resource_type.strip()
                    json_obj.setdefault("types", {})["resourceType"]=resource_type
                    json_obj.setdefault("types", {})["resourceTypeGeneral"]=resource_type_lookup[resource_type_general]
                    if format_type in iana_mime_type_lookup:
                        json_obj.setdefault("formats", []).append(iana_mime_type_lookup[format_type])
                    else:
                        logging.warn(f"Format {format_type} is not found in the lookup for row {index +1}.")
                else:
                    logging.warn(f"Resource type {resource_type_general} is not found in the lookup for row {index + 1}.")
            else:
                logging.info(f"sm: Format and/or sm:Format not found in row {index + 1}.")
    return json_list

#this function matches "sm:Creator" to creators and splits it.
def creators(json_list):
    for index, json_obj in enumerate(json_list):
        # Retrieve the contracting officer names for this row
        officer_names = set(json_obj.get("_contracting_officer_names", [])) 
        
        if "sm:Creator" in json_obj or "Personal Creator(s)" in json_obj:
            creators = json_obj.pop("sm:Creator", json_obj.pop("Personal Creator(s)", ""))
            creators = creators.split("\n") if creators else []
            for creator in creators:
                creator = creator.strip()
                parts = creator.split(",")
                
                if len(parts) == 2:
                        last_name, first_name = parts
                elif len(parts) > 2:
                    last_name, first_name = parts[0], " ".join(parts[1:])
                else:
                    logging.error(f"Unexpected format for creator: {creator}")
                    continue # Skip to the next creator
                
                first_name = first_name.strip()
                last_name = last_name.strip()
                
                ORCID = None
                if "|" in first_name:
                    first_name, ORCID = first_name.split("|")
                    ORCID = ORCID.strip()
                    if not ORCID.startswith("https://orcid.org/"):
                        ORCID = "https://orcid.org/" + ORCID
                if " (ORCID:" in first_name:
                    first_name, ORCID = first_name.split("(")
                    ORCID = ORCID.strip()
                    if ("ORCID: ") in ORCID:
                        ORCID = ORCID.replace("ORCID: ","")
                        ORCID = ORCID.strip()
                    if ORCID.endswith(")"):
                        ORCID = ORCID.replace(")", "")
                    if not ORCID.startswith("https://orcid.org/"):
                        ORCID = "https://orcid.org/" + ORCID
                
                # Skip if the creator is already a contracting officer
                if (last_name, first_name) in officer_names:
                    logging.info(f"Skipping duplicate creator '{first_name} {last_name}' (already a contracting officer).")
                    continue
                
                entry = {
                    "name": last_name.strip() + ", " + first_name.strip(),
                    "nameType": "Personal", 
                    "givenName": first_name, 
                    "familyName": last_name, 
                }
                
                if creator in orcids:
                    ORCID = orcids[creator][1]               
                
                if ORCID is not None:
                    entry['nameIdentifiers'] = [
                        {
                        "nameIdentifier": ORCID, 
                        "nameIdentifierScheme": "ORCID", 
                        "schemeUri": "https://orcid.org/"
                        }
                    ]
                json_obj.setdefault("creators", []).append(entry)
                
        else:
            logging.info(f"sm:Creator not found for row {index + 1}.")
    return json_list

def process_corporate_field(json_list, field_name, skip_ror_api=False):
    for index, json_obj in enumerate(json_list):
        if field_name in json_obj:
            corporate_values = json_obj.pop(field_name).split("\n")
            logging.debug("My object is " + str(corporate_values))
            for corporate_value in corporate_values:
                corporate_value = corporate_value.strip()
                ror_id, ror_name, affiliation_ror_id, affiliation_ror_name = get_ror_info(corporate_value, skip_ror_api)
                
                
                # Now define the field_mapping using corporate_value
                field_mapping = {
                    "sm:Corporate Creator": {
                        "name": corporate_value,
                        "key": "creators",
                        "nameType": "Organizational",
                    },
                    "sm:Corporate Contributor": {
                        "name": corporate_value,
                        "key": "contributors",
                        "nameType": "Organizational",
                        "contributorType": "Sponsor",
                    },
                    # TODO: decouple this into a new method, should look like {"publisher": {"name": "..."}}
                    "sm:Corporate Publisher": {
                        "name": corporate_value,
                        "key": "publisher",
                    },
                }

                output_structure = field_mapping.get(field_name, {})
                
                if ror_id:
                    if field_name == "sm:Corporate Publisher":
                        entry = {
                            "name": ror_name,
                            "schemeUri": "https://ror.org/",
                            "publisherIdentifier": ror_id,
                            "publisherIdentifierScheme": "ROR"
                        }
                    elif field_name == "sm:Corporate Contributor":
                        entry = {
                            "name": ror_name,
                            "nameType": "Organizational",
                            "contributorType": "Sponsor",
                            "nameIdentifiers": [
                                {
                                    "schemeUri": "https://ror.org/",
                                    "nameIdentifier": ror_id,
                                    "nameIdentifierScheme": "ROR"
                                }
                            ]
                        }
                    else:
                        entry = {
                            "name": ror_name,
                            "nameType": "Organizational",
                            "contributorType": "Sponsor",
                            "nameIdentifiers": [
                                {
                                    "schemeUri": "https://ror.org/",
                                    "nameIdentifier": ror_id,
                                    "nameIdentifierScheme": "ROR"
                                }
                            ]
                        }

                    # Include affiliation only if both are provided
                    if affiliation_ror_id and affiliation_ror_name:
                        entry["affiliation"] = [
                            {
                                "name": affiliation_ror_name,
                                "affiliationIdentifier": affiliation_ror_id,
                                "affiliationIdentifierScheme": "ROR"
                            }
                        ]
                else:
                    entry = {}
                    if affiliation_ror_id and affiliation_ror_name and ror_name:
                        entry = {
                            "name": ror_name,
                            "nameType": "Organizational",
                            "contributorType": "Sponsor",  # Or dynamically set if you support it
                            "affiliation": [
                                {
                                    "name": affiliation_ror_name,
                                    "affiliationIdentifier": affiliation_ror_id,
                                    "affiliationIdentifierScheme": "ROR"
                                }
                            ]
                        }
                    elif ror_name:
                        entry = {
                            "name": ror_name,
                            "nameType": "Organizational",
                            "contributorType": "Sponsor",
                        }
                    else:
                        entry = {
                            "name": corporate_value,
                            "nameType": "Organizational",
                            "contributorType": "Sponsor"  # again, dynamically set if needed
                        }
                    logging.info(f"ROR for {corporate_value} not found for row {index + 1}.")
                if "key" in output_structure:
                    key = output_structure["key"]

                    # If it's publisher, it should be a dict, not a list
                    if key == "publisher":
                        json_obj[key] = entry
                    else:
                        if key in json_obj:
                            if isinstance(json_obj[key], list):
                                json_obj[key].append(entry)
                            else:
                                # In case something unexpected sneaks in
                                json_obj[key] = [json_obj[key], entry]
                        else:
                            json_obj[key] = [entry]
    return json_list


def contracting_officer(json_list):
    for index, json_obj in enumerate(json_list):
        if "sm:Contracting Officer" in json_obj or "Contracting Officer" in json_obj:
            contracting_officers = json_obj.pop("sm:Contracting Officer", json_obj.pop("Contracting Officer", ""))
            contracting_officers = contracting_officers.strip()
            contracting_officers = contracting_officers.replace(";", "\n").split("\n") if contracting_officers else []
            logging.debug(print(f"I am getting stuck on line {index +1}"))
            
            # Store contracting officer names for deduplication
            officer_names = set()

            for contracting_officer in contracting_officers:
                logging.debug(print(f"I have successfully gotten through line {index +1}"))
                contracting_officer = contracting_officer.strip()
                last_name, first_name = contracting_officer.split(",")
                last_name = last_name.strip()
                first_name = first_name.strip()
                logging.debug(print(f"I Made it inside the for loop for line {index}"))

                if "|" in first_name:
                    first_name, ORCID = first_name.split("|")
                    ORCID = ORCID.strip()
                    if ORCID.startswith("(ORCID: "):
                        ORCID = ORCID.replace("(ORCID: ","")
                    if not ORCID.startswith("https://orcid.org/"):
                        ORCID = "https://orcid.org/" + ORCID
                    json_obj.setdefault("contributors", []).append({
                        "name": last_name.strip() + ", " + first_name.strip(),
                        "nameType": "Personal",
                        "givenName": first_name,
                        "familyName": last_name,
                        "contributorType": "Other",
                        "nameIdentifiers": [
                            {"nameIdentifier": ORCID, "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org/"}
                        ]})
                    
                if contracting_officer in orcids:
                    ORCID = orcids[contracting_officer][1]    
                    json_obj.setdefault("contributors", []).append({
                    "name": last_name.strip() + ", " + first_name.strip(),
                    "nameType": "Personal",
                    "givenName": first_name,
                    "familyName": last_name,
                    "contributorType": "Other",
                    "nameIdentifiers": [
                        {"nameIdentifier": ORCID, "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org/"}
                    ]})
                    
                else:
                    json_obj.setdefault("contributors", []).append({
                        "name": contracting_officer,
                        "nameType": "Personal",
                        "givenName": first_name,
                        "familyName": last_name,
                        "contributorType": "Other"
                    })
                officer_names.add((last_name, first_name))  # Add to deduplication set

            # Store contracting officers in the JSON for access in other functions
            json_obj["_contracting_officer_names"] = list(officer_names)  # Convert set to list
        else:
            logging.info(f"sm:Contracting Officer not found for row {index}.")
    return json_list


def contributors(json_list):
    for index, json_obj in enumerate(json_list):
        # Retrieve the contracting officer names for this row
        officer_names = set(json_obj.get("_contracting_officer_names", [])) 

        if "sm:Contributor" in json_obj or "Personal Contributor(s)" in json_obj:
            contributors = json_obj.pop("sm:Contributor", json_obj.pop("Personal Contributor(s)", ""))
            contributors = contributors.split("\n") if contributors else []
            logging.debug(print(f"I made it inside the if for {index +1}."))

            for contributor in contributors:
                contributor = contributor.strip()
                last_name, first_name = contributor.split(",")
                last_name = last_name.strip()
                first_name = first_name.strip()
                logging.debug(print(f"I am getting not getting stuck on line {index}"))

                ORCID = None
                if "|" in first_name:
                    first_name, ORCID = first_name.split("|")
                    ORCID = ORCID.strip()
                    if ORCID.startswith("(ORCID: "):
                        ORCID = ORCID.replace("(ORCID: ","")
                    if not ORCID.startswith("https://orcid.org/"):
                        ORCID = "https://orcid.org/" + ORCID
                    
                    
                # Skip if the contributor is already a contracting officer
                if (last_name, first_name) in officer_names:
                    logging.info(f"Skipping duplicate contributor '{first_name} {last_name}' (already a contracting officer).")
                    continue
                
                if contributor in orcids:
                    ORCID = orcids[contributor][1]      
                
                entry = {
                    "name": last_name.strip() + ", " + first_name.strip(),
                    "nameType": "Personal",
                    "givenName": first_name.strip(),
                    "familyName": last_name,
                    "contributorType": "Researcher",
                }
                
                if ORCID is not None:
                    entry['nameIdentifiers'] = [
                        {"nameIdentifier": ORCID, "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org/"}
                    ]
                json_obj.setdefault("contributors", []).append(entry)
        else:
            logging.info(f"sm:Contributor not found for row {index + 1}.")
    return json_list

# this function adds the NTL Data Curator generic email as the contact person for the DOI
def contact_point(json_list):
    for index, json_obj in enumerate(json_list):
        poc = None
        for candidate_key in ("Point of Contact", "Contact Person", "Contact", "POC"):
            if candidate_key in json_obj:
                poc = json_obj.pop(candidate_key)
                break
        if poc is not None:
            poc = poc.strip()
            last_name, first_name = poc.split(",")
            last_name = last_name.strip()
            first_name = first_name.strip()
            logging.debug(print(f"I am getting not getting stuck on line {index}"))
            if poc in orcids:
                ORCID = orcids[poc][1]  
                json_obj.setdefault("contributors", []).append({
                "name": last_name.strip() + ", " + first_name.strip(),
                "nameType": "Personal",
                "givenName": first_name.strip(),
                "familyName": last_name,
                "contributorType": "ContactPerson",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": ORCID,
                        "nameIdentifierScheme": "ORCID", 
                        "schemeUri": "https://orcid.org/"
                    }
                ]
                })
                logging.info(f"Contact Person found for row {index +1}.")
            else:
                json_obj.setdefault("contributors", []).append({
                "name": last_name.strip() + ", " + first_name.strip(),
                "nameType": "Personal",
                "givenName": first_name.strip(),
                "familyName": last_name,
                "contributorType": "ContactPerson",
                })
                logging.info(f"Contact Person found for row {index +1}.")
        # else:
        #     json_obj.setdefault("contributors", []).append({
        #     "name": "National Transportation Library",
        #     "nameType": "Organizational",
        #     "contributorType": "ContactPerson",
        #     "nameIdentifiers": [
        #         {
        #             "nameIdentifier": "https://ror.org/00snbrd52",
        #             "nameIdentifierScheme": "ROR",
        #             "schemeUri": "https://ror.org/"
        #         }
        #     ]
        # })
        logging.info(f"Using default NTL contact info for row {index + 1}.")
    return json_list
        

#loading TRT file
directory = "TRT"
files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".xlsx")]

if files:
    # Find the newest file by modification time
    newest_file = max(files, key=os.path.getmtime)
    logging.info(f"Selecting file {newest_file} for TRT import.")
else:
    logging.warn(f"No TRT file found in TRT folder.")

trt_data = pd.read_excel(newest_file)

# Combining all "Concept" columns (B to M) to find the first non-empty term, bypassing hierarchy
concept_columns = trt_data.loc[:, 'concept':'concept.11'] 

# Apply a function that finds the first non-empty value in each row of concept columns
trt_data['concept'] = concept_columns.apply(lambda row: next((term for term in row if pd.notna(term)), None), axis=1)

# Extracting needed columns for term and URI, replaces URI from Closed Pool Party API Link to Public Terms URI
trt_terms_df = trt_data[['uri', 'concept']].dropna(subset=['uri', 'concept'])
trt_terms_df['uri'] = trt_terms_df['uri'].str.replace(
    "https://km.nationalacademies.org/TRT-developmentv6/",
    "https://trt.trb.org/term/"
)

# Creating a keywords dictionary with TRT term validation and adding URI classificationCode
trt_lookup = dict(zip(trt_terms_df['concept'].str.strip().str.lower(), trt_terms_df['uri']))

def keywords(json_list):
    for index, json_obj in enumerate(json_list):
        if "sm:Key words" in json_obj or "Keywords (TRT Term(s) and Subject Keywords concatenated)" in json_obj:
            keywords_str = json_obj.pop("sm:Key words", json_obj.pop("Keywords (TRT Term(s) and Subject Keywords concatenated)", None))
            if keywords_str.endswith(", "):
                    keywords_str = keywords_str[:-2]
            if ", " in keywords_str:
                keywords_str = keywords_str.replace(", ", "\n").strip()
            keywords_str = keywords_str.split("\n")
            for keyword in keywords_str:
                keyword = keyword.strip()
                trt_code = trt_lookup.get(keyword.lower())
                if trt_code:
                    json_obj.setdefault("subjects", []).append({
                        "subject": keyword,
                        "schemeUri": "https://trt.trb.org/",
                        "subjectScheme": "Transportation Research Thesaurus",
                        "classificationCode": trt_code
                    })
                else: logging.info(f"Term '{keyword}' is not found in the TRT and was excluded.")
        else: 
            logging.info(f"sm:Key words not found for row {index + 1}.")
    return json_list

#this function matches "sm:Report Number" to alternateIdentifier
def report_number(json_list):
    for json_obj in json_list:
        if "sm:Report Number" in json_obj or "Report Number(s)" in json_obj:    
            report_numbers = json_obj.pop("sm:Report Number", json_obj.pop("Report Number(s)", None))
            report_numbers = report_numbers.strip()
            report_numbers = report_numbers.split(";")
            for report_number in report_numbers:
                report_number = report_number.strip()
                json_obj.setdefault("alternateIdentifiers", []).append({
                    "alternateIdentifier": report_number, 
                    "alternateIdentifierType": "USDOT Report Number"
                })
    return json_list


# Load Contract/Funding Information
directory = "Funder Information"
file = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".xlsx")][0]

funding_data = pd.read_excel(file)

# Ensure we work with string values
funding_data["contract_number_stripped"] = funding_data["contract_number_stripped"].astype(str)

# Create a lookup dictionary from the Excel file
funding_lookup = {
    row["contract_number_stripped"]: {
        "funderName": row["funder_name"],
        "awardNumber": row["contract_number_preferred"],
        "funderIdentifier": row["funder_identifier"],
        "funderIdentifierType": "ROR",
        "awardURI": row["contract_uri"],
        "awardTitle": row["contract_title"]
    }
    for _, row in funding_data.iterrows()
}


# Function to normalize contract number
def normalize_contract_number(contract_number):
    if "69A" in contract_number:
        contract_number = contract_number[contract_number.index("69A"):]
    return contract_number.replace("-", "").strip()


# Main function to apply to your JSON list
def contract_number(json_list):
    for json_obj in json_list:
        contract_field = None
        if "Grants, Contracts, Cooperative Agreements" in json_obj:
            contract_field = "Grants, Contracts, Cooperative Agreements"
        elif "Contract Number(s)" in json_obj:
            contract_field = "Contract Number(s)"

        if contract_field:
            raw_contracts = json_obj.pop(contract_field, "")
            for contract_number in raw_contracts.split(";"):
                contract_number = contract_number.strip()
                normalized = normalize_contract_number(contract_number)

                if normalized in funding_lookup:
                    # Use info from Excel
                    json_obj.setdefault("fundingReferences", []).append(funding_lookup[normalized])
                else:
                    # Default fallback
                    json_obj.setdefault("fundingReferences", []).append({
                        "funderName": "U.S. Department of Transportation",
                        "awardNumber": contract_number,
                        "funderIdentifier": "https://ror.org/02xfw2e90",
                        "funderIdentifierType": "ROR"
                    })
    return json_list


#this function matches "sm:ResearchHub ID" to alternateIdentifier
def researchHub_id(json_list):
    for json_obj in json_list:
        if "sm:ResearchHub ID" in json_obj or "ResearchHub ID" in json_obj:
            researchhub_id = json_obj.pop("sm:ResearchHub ID", json_obj.pop("ResearchHub ID", None))
            researchhub_id = researchhub_id.strip()
            json_obj.setdefault("alternateIdentifiers", []).append({
                "alternateIdentifier": researchhub_id, 
                "alternateIdentifierType": "USDOT ResearchHub Display ID"})
    return json_list

#this function matches "Content Notes" to "Descriptions"/TechnicalInfo
def content_notes(json_list):
    for json_obj in json_list:
        curation_note_level_b = "B. Logical-Technical Curation."
        curation_note_level_a = "A. Active Preservation"
        if "Content Notes" in json_obj or "Public Note" in json_obj:
            content_note = json_obj.pop("Content Notes", json_obj.pop("Public Note", None)).strip()
            json_obj.setdefault("descriptions", []).append({
                "lang": "en", 
                "description": content_note, 
                "descriptionType": "TechnicalInfo"
                })
            if curation_note_level_b in content_note or curation_note_level_a in content_note:
                json_obj.setdefault("contributors", []).append({
                    "name": "Tvrdy, Peyton", 
                    "nameType": "Personal", 
                    "givenName": "Peyton", 
                    "familyName": "Tvrdy", 
                    "contributorType": "DataCurator", 
                    "nameIdentifiers": [
                        {"nameIdentifier": "https://orcid.org/0000-0002-9720-4725", "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org/"}
                    ]  
                })
        if "Source" in json_obj:
            source_note = json_obj.pop("Source").strip()
            json_obj.setdefault("descriptions", []).append({
                "lang": "en",
                "description": source_note,
                "descriptionType": "TechnicalInfo"
            })
        if "Table of Contents" in json_obj:
            toc = json_obj.pop("Table of Contents").strip()
            json_obj.setdefault("descriptions", []).append({
                "lang": "en",
                "description": toc,
                "descriptionType": "TechnicalInfo"
            })
    return json_list

# this function matches Rights Statements to licenses
def rights(json_list):
    for index, json_obj in enumerate(json_list):
        rights_key = None
        for candidate_key in ("sm:Rights Statement", "Rights Statement", "Rights_Statement", "Copyright"):
            if candidate_key in json_obj:
                rights_key = candidate_key
                break
        if rights_key is None:
            rights = "Public Domain"
        else:
            rights = json_obj.pop(rights_key)
        if "Attribution 4.0 International" in rights or "https://creativecommons.org/licenses/by/4.0/" in rights:
            json_obj.setdefault("rightsList", []).append({
                "rights": "Creative Commons Attribution 4.0 International",
                "rightsUri": "https://creativecommons.org/licenses/by/4.0/legalcode",
                "schemeUri": "https://spdx.org/licenses/",
                "rightsIdentifier": "cc-by-4.0",
                "rightsIdentifierScheme": "SPDX"
                })
        elif "Zero" in rights or "https://creativecommons.org/publicdomain/zero/1.0/" in rights:
            json_obj.setdefault("rightsList", []).append({
                "rights": "Creative Commons Zero v1.0 Universal",
                "rightsUri": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
                "schemeUri": "https://spdx.org/licenses/",
                "rightsIdentifier": "cc0-1.0",
                "rightsIdentifierScheme": "SPDX"
                })
        elif "National Renewable Energy Laboratory Dataset License" in rights or "NREL" in rights:
            json_obj.setdefault("rightsList", []).append({
                "rights": "National Renewable Energy Laboratory Dataset License",
                "rightsUri": "https://data.nrel.gov/node/287/license",
                })
        elif "http://www.usa.gov/publicdomain/label/1.0/" in rights or "USA Governement Copyright" in rights: 
            json_obj.setdefault("rightsList", []).append({
                "rights": "United States Government Public Domain License",
                "rightsUri": "http://www.usa.gov/publicdomain/label/1.0/",
                })
        elif "Apache License Version 2.0" in rights or "https://www.apache.org/licenses/LICENSE-2.0" in rights: 
            json_obj.setdefault("rightsList", []).append({
                "rights": "Apache License 2.0",
                "rightsUri": "http://www.apache.org/licenses/LICENSE-2.0",
                "schemeUri": "https://spdx.org/licenses/",
                "rightsIdentifier": "apache-2.0",
                "rightsIdentifierScheme": "SPDX"
            })
        elif "Public Domain" in rights or "Open Access" in rights:
            json_obj.setdefault("rightsList", []).append({
                "rights": "Creative Commons Public Domain Dedication and Certification",
                "rightsUri": "https://creativecommons.org/publicdomain/mark/1.0/deed.en",
                "schemeUri": "https://spdx.org/licenses/",
                "rightsIdentifier": "cc-pdm-1.0",
                "rightsIdentifierScheme": "SPDX"
            })
        else:
            logging.info(f"No license or rights statement for row {index + 1}.")
    return json_list

def personal_publisher(json_list):
    for index, json_obj in enumerate(json_list):
        if "Personal Publisher(s)" in json_obj and "sm:Corporate Publisher" not in json_obj:
            personal_publisher = json_obj.pop("Personal Publisher(s)").strip()
            
            # Ensure publisher is a dictionary with a "name" key
            json_obj["publisher"] = {"name": personal_publisher}
            
            logging.info(f"Personal Publisher found for row {index +1}.")
    return json_list
            
                
#this function matches "Language" to language
def language(json_list):
    for index, json_obj in enumerate(json_list):
        if "Language" in json_obj or "Language(s)" in json_obj:
            languages = json_obj.pop("Language", json_obj.pop("Language(s)", None))
            languages = languages.replace(";", "\n")
            languages = languages.split("\n")
            for language in languages:
                language = language.strip()
                if language in language_dict:
                    json_obj["language"]=language_dict[language]
                else:
                    logging.warn(f"Language {language} not found in language dictionary for row {index + 1}.")
        else:
            logging.info(f"Language not found for row {index + 1}.")
    return json_list

#this function matches "Edition" to version
def edition(json_list):
    for json_obj in json_list:
        if "sm:Edition" in json_obj or "Edition" in json_obj:
            version = json_obj.pop("sm:Edition", json_obj.pop("Edition", None))
            version = version.strip()
            json_obj["version"]=version
    return json_list

#this function matches Series and their DOIs to IsPartOf to the correct related identifier structure
def series(json_list):
    for index, json_obj in enumerate(json_list):
        if "Series Name" in json_obj or "Is Part of" in json_obj:
            series_dois = json_obj.pop("Series Name", json_obj.pop("Is Part of", ""))
            series_dois = series_dois.replace(";", "\n")
            series_dois = series_dois.split("\n") if series_dois else []
            for series_doi in series_dois:
                if series_doi in series_to_doi_lookup:
                    # Create a new DOI-related entry
                    doi_entry_series = {
                        "relatedIdentifierType": "DOI", 
                        "relatedIdentifier": series_to_doi_lookup[series_doi], 
                        "relationType": "IsPartOf",
                        "resourceTypeGeneral": "Collection"
                    }
                    # Initialize "related_identifiers" if not already present
                    json_obj.setdefault("relatedIdentifiers", []).append(doi_entry_series)
                else:
                    logging.warn(f"Series {series_doi} not found in series dictionary for row {index + 1}.")
    return json_list

#this function matches "Description" to "Descriptions"/Abstract
def description(json_list):
    for index, json_obj in enumerate(json_list):
        require("types" in json_obj, "Resource Type wasn't called yet")
        if "Description" in json_obj or "Abstract" in json_obj:
            description = json_obj.pop("Description", json_obj.pop("Abstract", None))
            if "resourceTypeGeneral" == "Collection":
                json_obj.setdefault("descriptions", []).append({
                "lang": "en", 
                "description": description, 
                "descriptionType": "SeriesInformation"
                })
            else:
                json_obj.setdefault("descriptions", []).append({
                    "lang": "en", 
                    "description": description, 
                    "descriptionType": "Abstract"
                    })
        else:
            logging.info(f"Description not found for row {index + 1}.")
    return json_list

# this function declares the schema version at the end of the payload. This statement is required for objects to be accepted by the DataCite API
def schema(json_list):
    for json_obj in json_list:
        json_obj['schemaVersion'] = "https://schema.datacite.org/meta/kernel-4.6/"
    return json_list

# This function will drop unnecessary information
def drop_and_pop(json_list):
    for json_obj in json_list:
        if "_contracting_officer_names" in json_obj:
            json_obj.pop("_contracting_officer_names")
        if "state" in json_obj:
            json_obj.pop("state")
    return json_list

# this function wraps the entire payload in the "data" structure with the type of "dois". This also puts all the metadata created in the process into the object "attributes."
def wrap_object(json_list):
    output_list = list()
    for json_obj in json_list:
        output_obj = {"data": {"type": "dois", "attributes": json_obj}}
        output_list.append(output_obj)
    return output_list

def require(condition, description):
    if not condition:
        raise Exception(description)
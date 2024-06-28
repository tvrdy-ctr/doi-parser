import codecs
import csv
import sys
import json
import logging
import requests
from post_processes import (
    document_urls,
	workroom_id,
	ROSAP_ID,
	ROSAP_URL,
	sm_Collection,
	sm_digital_object_identifier,
	title,
	alt_title,
	publication_date,
	resource_type,
	creators,
	corporate_creator,
	process_corporate_field,
	contributors,
	keywords,
	report_number,
	contract_number,
	researchHub_id,
	content_notes,
	language,
	edition,
	series,
 	description
)

# TODO: rename process.log to something more palatable
logging.basicConfig(handlers=[logging.StreamHandler(), logging.FileHandler('default_process.log')], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# DOI Prefix for the testing environment
doi_prefix = "10.80510" # TODO: do i need this?

""""""	
def unit_test():
    #opening and reading csv and json versions of the unit test
	csv_fp = open('test/unit test input.csv', 'r', encoding='utf-8')
	json_fp = open('test/unit test output.json', 'r', encoding='utf-8')

	expected_output = json.load(json_fp)

	#declaring that the csv unit test should be converted to json through the csv reader and be the model for the post process output
	test_output = corporate_creator(csv_to_json(csv.reader(csv_fp)))

	csv_fp.close()
	json_fp.close()

	#testing if the expected output of the program matches the unit test.
	try:
		assert expected_output == test_output
  	#if they don't match, the test and expected output are both printed so the user can evaluate the difference between what they submitted and the unit test
	except AssertionError as e:
		print("Expected Output:", expected_output)
		print("Actual Output:", test_output)
		raise e
""""""

#this function converts the csv file to json
def csv_to_json(csv_reader):
	output = []
	header_row = True
	keys = {}

	#this takes each row, strips it of extra spaces, creates an array for each row, with each value in the array representing a column
	for row in csv_reader:
		if header_row:
			logging.info("=> Parsing CSV")
			row[0] = row[0].strip(codecs.BOM_UTF8.decode(sys.stdin.encoding))
			keys = {i:row[i].strip() for i in range(len(row)) if row[i] != ''}

			header_row = False
			continue

		#for each row, makes each key an element, and stops when out of rows, then returning the output
		output_obj = {}
		for i in range(len(keys)):
			key = keys[i]
			element = row[i]

			if element != ''.strip():
				output_obj[key] = element
		
		if output_obj != {}:
			output.append(output_obj)

	return output
    

def main():
	#unit_test()

	# TODO: have some default logging configuration incase i don't have a filename

	if len(sys.argv) != 2:
		logging.error("Error: Please provide a filename")
		handlers= logging.StreamHandler(), logging.FileHandler('system_failure_process.log')
		logging.getLogger().addHandler(handlers)
		sys.exit(1)

	# TODO: configure logger based on input file name

	handlers = logging.StreamHandler(), sys.argv[1].rstrip('csv') + 'log'

	logging.info("=> Starting File Read: %s" % sys.argv[1])
	fp = open(sys.argv[1], 'r', encoding='utf-8')

	
	output = csv_to_json(csv.reader(fp))
	for func in (document_urls,
     		workroom_id,
			ROSAP_ID,
			ROSAP_URL,
			sm_Collection,
			sm_digital_object_identifier,
			title,
			alt_title,
			publication_date,
			resource_type,
			creators,
			process_corporate_field,
			contributors,
			keywords,
			report_number,
			contract_number,
			researchHub_id,
			content_notes,
			language,
			edition,
			series,
			description):
		output = func(output)
			
	fp.close()
	logging.info("=> Finished Parsing\n")
	print(json.dumps(output[0], indent=2))
	should_continue = input("\n=> Does the above look good? [y/N]: ").upper() == 'Y'

	if not should_continue:
		print("Aborting...")
		sys.exit(2)

	out_filename = sys.argv[1].rstrip('csv') + 'json'
	logging.info("=> Starting Output Write: %s " % out_filename)
	
	fpo = open(out_filename, 'w')
	json.dump(output, fpo, indent=2)
 

	should_continue = input("\n=> Do you want to send the request now? [y/N]: ").upper() == 'Y'

	if not should_continue:
		logging.info("=> Done !")
		sys.exit(0)

	logging.info("=> Preparing Request")

	url = "https://api.test.datacite.org"
	payload = json.dumps(output)
 
	# Read username and password from config.txt
	with open("config.txt", "r") as config_file:
		config_lines = config_file.readlines()
		for line in config_lines:
			if line.startswith("username"):
				username = line.split("=")[1].strip()
			elif line.startswith("password"):
				password = line.split("=")[1].strip()
 
	# Encode username and password for Basic Authentication
	auth_header = codecs.encode(f"{username}:{password}", 'base64').decode().replace('\n', '')
 
	headers = {
		'Authorization': 'Basic ' + auth_header,
		'Content-Type': 'application/vnd.api+json',
	}

	logging.info("=> Sending Request")
	response = requests.request("POST", url, headers=headers, data=payload)

	logging.info("=> Handling Response: %s" % response.status_code)
	if response.status_code != 200:
		logging.error("=> POST did not fire successfully! %s" % response.status_code)
	else:
		logging.info("=> Writing Response to file")
		fpo.write('\n\n---------------------------------------------------------------------------------\n\nRESULTS\n\n')
		json.dump(response.json(), fpo, indent=2)
		fpo.close()
		logging.info("=> Done !")
	

if __name__ == '__main__':
	main()
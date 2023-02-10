import csv
from collections import defaultdict
import sys
import os
import re

# if len(sys.argv) < 2:
#     print("Error: No teamname-quadrant provided ex : qira-q1")
#     sys.exit(1)

# team_quadrant = sys.argv[1].strip().lower()
team_quadrant = 'qira-q1'

# List of keywords to filter by
test_file_paths = ["/test/", "unit", "__test__"]
cl_file_map = {}

def format_cl_output():
    # Read the contents of the perforce file generated in the getPerforceCLDetails.sh
    with open(team_quadrant + "-manual-perforce-cls.txt", "r") as infile:
        perforce_output = infile.readlines()

    for line in perforce_output:
        match = re.search(r'(.*?)#.* -.* (\d+)', line)
        if match:
            file_path = match.group(1)
            changelist_id = match.group(2)
            #exclude any freeze branch integration
            if not('freeze' in file_path.casefold()):
                # check if file path contains any of the keywords
                if any(keyword in file_path for keyword in test_file_paths):
                    if changelist_id in cl_file_map:
                        cl_file_map[changelist_id].append(file_path)
                    else:
                        cl_file_map[changelist_id] = [file_path]

    # Open a new CSV file for writing
    with open(team_quadrant + "-formatted-perforce-cl-details.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Perforce_Changelist__c", "File Path"]) # write the header row
        for changelist_id, value in cl_file_map.items():
            for file_path in value:
                writer.writerow([changelist_id, file_path]) # write the data row

def build_column(items_set):
    column = "<td>"
    for items in items_set:
        for item in items:
            column += "<li>{}</li>".format(item)
    column += "</td>"
    return column

def build_href_column_set_of_sets(items_set, href_url):
    column = "<td>"
    for items in items_set:
        for item in items:
            column += "<li><a href='{}{}'>{}</a></li>".format(href_url, item, item)
    column += "</td>"
    return column

def build_test_scenario_column(items_set, manual_test_scenario_map, href_url):
    column = "<td>"
    for item in items_set:
        column += "<li><a href='{}{}'>{}</a></li>".format(href_url, item, next(iter(get_value_from_map_of_maps(manual_test_scenario_map, str(item[:-3]), "Test Scenario Name"))))
    column += "</td>"
    #Product Tag column
    column += "<td>"
    column += next(iter(get_value_from_map_of_maps(manual_test_scenario_map, str(item[:-3]), 'Product Tag')))
    column += "</td>"
    # Owner and Created Column
    column += "<td>"
    column += next(iter(get_value_from_map_of_maps(manual_test_scenario_map, str(item[:-3]), 'Test Scenario: Owner Name'))) +\
                " / " + next(iter(get_value_from_map_of_maps(manual_test_scenario_map, str(item[:-3]), 'Test Scenario: Created By')))
    column += "</td>"
    return column

def getStyles():
    return '''<style> table, th, td {
                border: 1px solid black;
                 border-collapse: collapse;
            }
            th {
                font-size: 12px;
            } 
            td {
                font-size: 11px;
            }
            </style>'''

def get_value_from_map_of_maps(map_data, key, value_col):
    if map_data.get(key) is not None:
        return map_data[key][value_col]
    else:
        return "No Data exists"

# Function to generate the HTML table
def generate_html_table(data_map, manual_test_scenario_map, test_suite_test_scenario_map):
    html = "<table>"
    html += getStyles()

    header = "<tr><th>Test Suite ID</th>"
    header += "<th>Test Scenarios</th>"
    header += "<th>Product Tag</th>"
    header += "<th>Test Scenario: Owner/Created By</th>"
    header += "<th>Work Item ID</th>"
    header += "<th>Change List</th>"
    header += "<th>CL Test Files</th>"
    header += "</tr>"

    rows = ""
    for test_suite_id, values in data_map.items():
        row = "<tr><td><a href='https://gus.lightning.force.com/{}'>{}</a></td>"\
            .format(test_suite_id, next(iter(get_value_from_map_of_maps(test_suite_test_scenario_map, test_suite_id, "Test_Suite_Name__c"))))
        
        test_scenario_ids = get_value_from_map_of_maps(test_suite_test_scenario_map, test_suite_id, "Test_Scenario__c")

        # for scenario_id in test_scenario_ids:
        row += build_test_scenario_column(test_scenario_ids, manual_test_scenario_map, 'https://gus.lightning.force.com/')

        # for index, value in enumerate(values):
        for index in range(len(values)):
            #Work ID
            if(index == 0):
                row += build_href_column_set_of_sets(values[0], 'https://gus.lightning.force.com/')
            #CL ID
            elif(index == 1):    
                cl_files_list = values[1];

                cl_set = cl_files_list[0][0]
                if (cl_set is not None):
                    if len(cl_set):
                        row += build_href_column_set_of_sets(cl_set, "https://swarm.soma.salesforce.com/changes/")
                    else:
                        row += "<td>" + str(cl_files_list) + "</td>"
                    
                    file_set = cl_files_list[0][1]
                    if len(file_set) > 0:
                        row += build_column(file_set)
                    else:
                        row += "<td>No tests written</td>"

            elif(index == 2):
                row += "<td>"
                for v in values[2]:
                    row += "<li>{}</li>".format(v)
                row += "</td>"
            
        row += "</td></tr>"
        rows += row

    html += "{}{}</table>".format(header, rows)
    return html

def generate_map_from_csv(file_path, key_column):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        key_index = header.index(key_column)
        data_map = {}
        for row in reader:
            key = row[key_index]
            values = row[:key_index] + row[key_index + 1:]
            if key in data_map:
                data_map[key].update(values)
            else:
                data_map[key] = set(values)
    return data_map

def generate_map_of_maps_from_csv(file_path, key_col, value_cols):
    map_data = {}
    with open(file_path, newline='', encoding='iso-8859-1') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        key_col_index = header.index(key_col)
        value_col_indices = [header.index(col) for col in value_cols]
        for row in reader:
            key = row[key_col_index]
            values = {header[index]: row[index] for index in value_col_indices}
            if key in map_data:
                for value_col in value_cols:
                    if value_col in map_data[key]:
                        map_data[key][value_col].update({values[value_col]})
                    else:
                        map_data[key][value_col] = {values[value_col]}
            else:
                for value_col in value_cols:
                    values[value_col] = {values[value_col]}
                map_data[key] = values
    return map_data

def combine_maps(map1, map2):
    combined_map = {}
    for key, values1 in map1.items():
        combined_values = []
        for value1_item in values1:
            values2 = map2.get(value1_item, [None])
            combined_values.append(values2)
        combined_map[key] = [[values1]] + [combined_values]
    return combined_map

# Format perforce.txt into a readable csv
format_cl_output()

# Read the data from the CSV files and combine them
data = defaultdict(list)
columns = set()
#key_column = "Test Scenario: ID" # the column name used as the key to group the rows

# Get the list of all test scenarios in a map keyed by test scenario id
manual_test_scenario_map = generate_map_of_maps_from_csv(team_quadrant + "-manual-test-scenarios.csv", "Test Scenario: ID", \
    ["Test Scenario: Test Scenario ID", "Test Scenario Name", "Product Tag","Test Scenario: Owner Name","Test Scenario: Created By"])

# Get the list of test suites associated with each test scenario
test_suite_test_scenario_map = generate_map_of_maps_from_csv(team_quadrant + "-test-scenario-test-suite.csv", "Test_Suite__c", ["Test_Suite_Name__c", "Test_Scenario__c"])

# Get the list of WI associated with each test suite
test_suite_work_map = generate_map_from_csv(team_quadrant + "-test-suite-work-id.csv", "Test_Suite__c")
# Get the list of all CL's associated with a WI
work_cl_map = generate_map_from_csv(team_quadrant + "-work-id-cl.csv", "Work__c")
# Get the list of test files associated with each CL
cl_test_files_map = generate_map_from_csv(team_quadrant + "-formatted-perforce-cl-details.csv", "Perforce_Changelist__c")
work_cl_files_map = combine_maps(work_cl_map, cl_test_files_map)

# Get a map keyed of Test Scenario and all suite associated, also since Test suite are mapped to WI, we can get those as well
test_suite_work_cl_files_map = combine_maps(test_suite_work_map, work_cl_files_map)
html = generate_html_table(test_suite_work_cl_files_map, manual_test_scenario_map, test_suite_test_scenario_map)

with open(team_quadrant + "-wi-cl-ts-report.html", "w") as file:
   file.write(html)
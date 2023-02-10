import csv
import subprocess
import glob
import sys

# if len(sys.argv) < 2:
#     print("Error: No teamname-quadrant provided ex : qira-q1")
#     sys.exit(1)

# team_quadrant = sys.argv[1].strip().lower()
team_quadrant = 'r2d2-q2'

def get_column_values_from_file(file_name, column_name):
    values = []

    with open(file_name, 'r', encoding='iso-8859-1') as file:
        reader = csv.DictReader(file)
        for row in reader:
            values.append(row[column_name])

    return values

def get_column_values_from_file_as_CSV(file_name, column_name):
    return "'" + "','".join(get_column_values_from_file(file_name, column_name)) + "'"


def get_csv_from_list(list):
    return ",".join(list)

def execute_soql(query, output_file):
    query = subprocess.run(f'sfdx force:data:soql:query -q "' + query + '" -r csv > '+ output_file +'', shell=True, universal_newlines=True).stdout
    print("Completed generation of " + output_file)

# def getTeamAndQuadrant(file_path):
#     match = re.search(r'\w*-q\w+', file_path)
#     if match:
#         team = match.group()
#         return team

def split_into_batches(string, batch_size):
    elements = string.split(',')
    return [elements[i:i + batch_size] for i in range(0, len(elements), batch_size)]

def combine_csv_files(filenames, output_filename):
    with open(output_filename, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        first_file = True
        for filename in filenames:
            with open(filename, 'r') as f_in:
                reader = csv.reader(f_in)
                if first_file:
                    for row in reader:
                        writer.writerow(row)
                    first_file = False
                else:
                    header = next(reader)
                    for row in reader:
                        writer.writerow(row)

##### Get all test suites from test scenarios
test_scenario_file_name = team_quadrant + "-manual-test-scenarios.csv"

test_scenario_test_suite_file_name = team_quadrant + "-test-scenario-test-suite.csv"
test_scenario_column_name = "Test Scenario: ID" # the name of the column you want to get values from
test_scenario_ids = get_column_values_from_file_as_CSV(test_scenario_file_name, test_scenario_column_name)
test_scenario_id_batches = split_into_batches(test_scenario_ids, 100)
for idx, test_scenario_id_batch in enumerate(test_scenario_id_batches):
    test_scenario_test_suite_soql = "SELECT Test_Suite__c,Test_Suite_Name__c,Test_Scenario__c FROM ADM_Related_Test_Scenario__c where Test_Scenario__c in (" + get_csv_from_list(test_scenario_id_batch) + ")"
    execute_soql(test_scenario_test_suite_soql, test_scenario_test_suite_file_name + "." + str(idx))

file_names = glob.glob("*-test-scenario-test-suite.csv.[0-9]*")
combine_csv_files(file_names, test_scenario_test_suite_file_name)

##### Get all test work ids from test suites
test_suite_work_id_file_name = team_quadrant + "-test-suite-work-id.csv"
test_suite_column_name = "Test_Suite__c" # the name of the column you want to get values from
test_suite_ids = get_column_values_from_file_as_CSV(test_scenario_test_suite_file_name, test_suite_column_name)
test_suite_id_batches = split_into_batches(test_suite_ids, 100)
for idx, test_suite_id_batch in enumerate(test_suite_id_batches):
    test_suite_work_id_soql = "SELECT Test_Suite__c,Work__c FROM ADM_Related_Test_Suite__c WHERE Test_Suite__c IN (" + get_csv_from_list(test_suite_id_batch) + ")"
    execute_soql(test_suite_work_id_soql, test_suite_work_id_file_name + "." + str(idx))

file_names = glob.glob("*-test-suite-work-id.csv.[0-9]*")
combine_csv_files(file_names, test_suite_work_id_file_name)

##### Get all cls from work ids
work_id__cl_file_name = team_quadrant + "-work-id-cl.csv"
work_column_name = "Work__c" # the name of the column you want to get values from
work_ids = get_column_values_from_file_as_CSV(test_suite_work_id_file_name, work_column_name)
#only check where source is perforce
work_id_batches = split_into_batches(work_ids, 100)
for idx, work_id_batch in enumerate(work_id_batches):
    work_ids_cl_soql = "SELECT Work__c,Perforce_Changelist__c FROM ADM_Change_List__c WHERE Work__c IN (" + get_csv_from_list(work_id_batch) + ") AND Source__c = 'Perforce'"
    execute_soql(work_ids_cl_soql, work_id__cl_file_name + "." + str(idx))

file_names = glob.glob("*-work-id-cl.csv.[0-9]*")
combine_csv_files(file_names, work_id__cl_file_name)

perforce_cl_ids=get_column_values_from_file(work_id__cl_file_name, "Perforce_Changelist__c")
# print("-------------------------------CL ID--------------------------------------------------------------")
# print(perforce_cl_ids)
with open(team_quadrant + "-cl.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(perforce_cl_ids)

print("Completed generation of " + team_quadrant + "-cl.csv")

#Run the python script and get the CL details in a text file format
# once you have that text file - ensure you have the right name and then then call generateHTMLReport.py


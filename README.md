# test-scenario-dev-automation-report

To get the final output as a HTML report follow the following steps
* Get a team specific q1 or q2 manual test cases from the [taleggio debt report](https://gus.lightning.force.com/lightning/r/Dashboard/01ZEE000000Vg2z2AC/view?queryScope=userFolders)
* Export the report as a CSV to a file called `<team-name>-<quadrant>-manual-test-scenarios.csv`
* Run `getWorkItemIdsFromTestScenario.py` with an argument `<team-name>-<quadrant>`
* One of the files which is generated is of type `<team-name>-<quadrant>-cl.csv`
* Run `getPerforceCLDetails.py` with the CL list generated from the above program and concatenate the output to a txt file and name it `<team-name>-<quadrant>-manual-perforce-cls.txt`
* Now run `generateHTMLReport.py <team-name>-<quadrant>` which will generate a HTML file named `<team-name>-<quadrant>-wi-cl-ts-report.html` which you can then use to refer and mark things which are automated but marked as manual.

> I am using vscode and have the entire repo there and can run the code from the built in terminal.

* Sample input and output are in the sample folder

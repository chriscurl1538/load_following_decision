## Software Package: load_following_decision
### A How-to Guide with examples

Before proceeding with this document, make sure you have read 
the README.md and have followed all instructions contained within.

- Read the file's Installation Instructions and Getting Started 
sections carefully. 
- Verify that the package and its dependencies have been 
installed correctly. 
- Check that the energy demand file and .yaml file are located 
in the /input_files folder
- Verify that the .yaml file has been filled out correctly.

### Running the Program

**Step 1: Navigate to the desired folder**

This package is run from the command line. In your terminal, 
navigate to the /load_following_decision_package folder. This 
folder contains the test suite and package modules. For most 
terminals you can change directories using the following command:

`cd directory_path`

where directory_path is the absolute or relative path to the 
desired folder.

**Step 2: Run the program from the command line**

Run the file using the following command:

`python command_line.py --help`

This will print the following instructions for using the CLI.

    usage: command_line.py [-h] --in INPUT                   
                                                             
    Import equipment operating parameter data                
                                                             
    optional arguments:                                      
      -h, --help  show this help message and exit            
      --in INPUT  filename for .yaml file with equipment data

To run the program using the provided pre-filled .yaml file, 
enter the name of the .yaml file like this:

`python command_line.py --in default_file.yaml`

**Step 3: Verify output:**

Using the provided default files (.csv and .yaml) you should get
the tables and plots shown in /docs/example_output.md

### Testing the program

INSTRUCTIONS FOR USING TESTING SUITE HERE
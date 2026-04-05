detect_print.py is a python script that detects print and pprint function calls to avoid accedintially committing unintended prints
it reads every python file from the root of the project, fuzzy_chips/, this is one directory above the script location, the script is fuzzy_chips/dev_tools/detect_print.py it then list every print statement with the line number it occurs on
excludes the keyboard/ config_manager/ test/ dev_tools/ directories, and the my_logger.py file
the excluded list is a constant list near the top of the file

the output is in this format
file_path_from_project_root
line #line_number
line #line_number2
line #line_number3

other_file_path
line #line_number
line #line_number2
line #line_number3

only print and pprint statements are detected, 
they are not detected if they are inside a string, or a comment block.
there are not false positives for functions with print in the name like str.isprintable()


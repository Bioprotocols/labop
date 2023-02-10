
import difflib



def file_diff(comparison_file, temp_name):
    diffs = []
    with open(comparison_file) as file_1:
        file_1_text = file_1.readlines()

    with open(temp_name) as file_2:
        file_2_text = file_2.readlines()

    # Find and print the diff:
    for line in difflib.unified_diff(
            file_1_text, file_2_text, fromfile=comparison_file,
            tofile=temp_name, lineterm=''):
        diffs.append(line)
    return diffs

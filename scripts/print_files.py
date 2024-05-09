import sys
from typing import Optional


def print_file_contents(filename):
    """
    Function to print out the content of a file
    """
    try:
        with open(filename, "r") as file:
            print(file.read())
    except IOError:
        print(f"Error opening file: {filename}")


def main(file_names: Optional[list[str]] = None):
    """
    Main function
    """
    # Check if file names were passed as arguments

    if file_names is None:
        if len(sys.argv) <= 1:
            print("Usage: python3 print_files.py <filename1> <filename2> ...")
            sys.exit()
        else:
            file_names = sys.argv[1:]

    # Iterate through all file names passed as arguments
    for filename in file_names:
        print(f"```{filename}")
        print_file_contents(filename)
        print("```")


if __name__ == "__main__":
    file_names = [
        "kuloaikaleo/main.py",
        "kuloaikaleo/leo.py",
        "kuloaikaleo/kaaoao.py",
        "requirements.txt",
    ]
    main(file_names)

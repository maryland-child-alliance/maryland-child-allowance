import os
import pathlib


def rel_location(directory_name: str = "src") -> str:
    """Goes up until it finds the folder 'Input_Data', then it stops
    returns '' or '../' or '../../', or ... depending on how many times it had to go up"""
    path = pathlib.Path(__file__)
    num_tries = 5
    for num_up_folder in range(num_tries):
        path = path.parent
        if directory_name in os.listdir(path):
            break

    if num_tries == num_up_folder:
        raise FileNotFoundError(
            f"The directory '{directory_name}' could not be found in the 5"
            " directories above this file's location. "
        )
    location = "../" * num_up_folder
    return pathlib.Path(location)


if __name__ == "__main__":
    print(rel_location("docs"))
    print(rel_location("Input_Data"))
    print(rel_location())

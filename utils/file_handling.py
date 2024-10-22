import pickle
from typing import List

# Function to append new data to a pickled array
def append_to_pickled_array(file_path:str, new_data: List[dict]):
    # Load the existing array (if the file exists)
    try:
        with open(file_path, 'rb') as file:
            array = pickle.load(file)
    except (FileNotFoundError, EOFError):  # If the file does not exist or is empty
        array = []  # Start with an empty array

    # Append the new data to the array
    for data in new_data:
        array.append(data)

    # Save the updated array back to the file
    with open(file_path, 'wb') as file:
        pickle.dump(array, file)
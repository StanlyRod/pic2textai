from aiofile import AIOFile, Writer  # type: ignore 
import asyncio 
import os 
import base64 
import logging
import pyperclip # type: ignore
from rich import print
from rich.logging import RichHandler
import sys 
from openai import AsyncOpenAI  # type: ignore 
from pathlib import Path


# # Configure logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S",handlers=[RichHandler()] ) 

# Create logger
rich_logging = logging.getLogger("rich_logger")

# Set the logging level to INFO
def log_info(message: str):
    rich_logging.info(message)

# Set the logging level to ERROR
def log_error(message: str):
    rich_logging.error(message)


# Get the current working directory 
current_directory = os.getcwd() 

# File name
filename = "extractedtext.txt"

# joining the current directory with the text filename
text_file_path = os.path.join(current_directory, filename) 
 
 # get openai api key from environmental variable
openaikey = os.getenv("OPENAIKEY") 


# check for OpenAI API key and raise an exception if the environmental variable is not set
if not openaikey: 
    raise EnvironmentError("OPENAIKEY environment variable not set") 

client = AsyncOpenAI(api_key=openaikey) 

# function to append text to a text file 
async def append_to_file(path: str, text: str): 
    try: 
        async with AIOFile(path, "a") as afp: 
            writer = Writer(afp) 
            await writer(f"{text}\n") 
            await afp.fsync()
        log_info(f"Text appended to {path}") 
    except PermissionError:
        log_error(f"Permission denied: Unable to open file or the file is currently in use {path}. Please check file permissions.")
    except FileNotFoundError:
        log_error(f"File not found: {path}. Please ensure the file exists.")
    except Exception as e: 
        log_error(f"Failed to append to file: {e}") 

 

# encode image to base64
async def encode_image(image_path: str) -> str: 
    try: 
        async with AIOFile(image_path, "rb") as image_file: 
            content = await image_file.read()
        return base64.b64encode(content).decode("utf-8") 
    except Exception as e: 
        log_error(f"Failed to encode image {image_path}: {e}") 
        return "" 

 

# Asynchronous function to process the OpenAI API request 
async def analyze_image(image_path: str, prompt: str) -> str: 
    try: 
        # call the encode_image function to encode the image to base64
        base64_image = await encode_image(image_path) 

        if not base64_image: 
            return "Failed to encode image" 
        
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg"}.get(ext[1:], "image/png")
        
        response = await client.chat.completions.create( 
            model="gpt-4o", 
            messages=[ 
                { 
                    "role": "user", 
                    "content": [ 
                        {"type": "text", "text": f"{prompt}"}, 
                        { 
                            "type": "image_url", 
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}, 
                        }, 
                    ], 
                } 
            ], 
        ) 

        text_response = response.choices[0].message.content 

        text_response = text_response.encode("utf-8").decode("utf-8", errors="replace") 

        return text_response.replace("�", "'") 
    
    except Exception as e: 
        log_error(f"Failed to analyze image {image_path}: {e}") 
        return "Failed to analyze image" 
    

# read the text file
async def read_text_file(file_path):
    try:
        async with AIOFile(file_path, 'r') as text_file:
            # Read the content of the file
            content = await text_file.read()
        return content
    except FileNotFoundError:
        log_error(f"File not found: {file_path}. Please ensure the file exists.")
        return ""
    except PermissionError:
        log_error(f"Permission denied: Unable to read the file {file_path}. Please check file permissions.")
        return ""
    except Exception as e:
        log_error(f"An error occurred while reading the file {file_path}: {e}")
        return ""
    

# function to copy text to clipboard
async def copy_to_clipboard():
    # Read the text file
    content = await read_text_file(text_file_path)
    if content:
        # Copy the content to clipboard
        pyperclip.copy(content)
        log_info("Text copied to clipboard successfully.")
    else:  
        log_error("No content to copy to clipboard.")
        return


# Function to rename images in the with enumeration
async def rename_images_with_enumeration(folder_path: str):
    try:
        # Check if the images folder exists
        if not os.path.exists(folder_path):
            # Raise an error if the folder does not exist
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Initialize a counter for renaming images
        count_images = 1

        # Iterate through the files in the folder
        for each_image in os.listdir(folder_path):
            # Process only files with a ".png" extension
            if each_image.endswith((".png", ".jpeg", ".jpg")):
                try:
                    # Full path to the old image
                    old_path = os.path.join(folder_path, each_image)

                    # Generate a new name for the image (like: "1.png", "2.png", etc.)
                    new_name = f"{count_images}.png"
                    new_path = os.path.join(folder_path, new_name)

                    # Rename the file in place
                    os.rename(old_path, new_path)

                    # Log the renaming operation
                    log_info(f"Renamed {each_image} to {new_name}")
                    log_info("")

                    # Increment count 
                    count_images += 1
                except FileNotFoundError:
                    log_error(f"File not found: {each_image}. Skipping...")
                except PermissionError:
                    log_error(f"Permission denied: Unable to rename {each_image}. Skipping...")
                except Exception as e:
                    log_error(f"An error occurred while renaming {each_image}: {e}")
    except FileNotFoundError as e:
        log_error(e)
    except PermissionError:
        log_error(f"Permission denied: Unable to access the folder {folder_path}.")
    except Exception as e:
        log_error(f"An unexpected error occurred: {e}")


# Extracts the name of the file without its extension from the given file path.
async def get_image_name_without_extension(image_name_path: str) -> str:
    try:
        path = Path(image_name_path)
        return path.stem
    except Exception as e:
        log_error(f"An error occurred while extracting the file name: {e}")
        return ""
    

# Function to sort the dictionary by keys
async def sort_dictionary_by_keys(input_dict):
    sorted_dict = dict(sorted(input_dict.items()))
    values = sorted_dict.values()
    try:
        return values
    except Exception as e:
        log_error(f"An error occurred while writing to the file: {e}")
        return ""


# function to execute the main logic
async def execute(prompt: str = "Extract all the text from this image"):
    try: 
        ocr_dictionary = {}

        #=================================================================
        #joining the current directory with the folder
        create_directory = os.path.join(current_directory, "imagesfolder")

        # Create the directory by skipping errors
        os.makedirs(create_directory, exist_ok=True)
        #=================================================================

        images_folder = os.path.join(current_directory, "imagesfolder") 

        # Check if the "imagesfolder" directory exists
        if not os.path.exists(images_folder): 
            log_error(f"Folder not found: {images_folder}") 
            return # Exit the function if the folder doesn't exist
        
        await rename_images_with_enumeration(images_folder)

        # List all image files in the specified folder with extensions .png, .jpeg, or .jpg
        all_images = [each_image for each_image in os.listdir(images_folder) if each_image.lower().endswith((".png", ".jpeg", ".jpg"))]

        # Count the total number of files in the "imagesfolder" directory
        total_images =  len(all_images)

        # Log the total number of images to be analyzed
        log_info(f"Total images to be analyze: {total_images}")

        async def process_image(image_file:str):
            try:
                image_path = os.path.join(images_folder, image_file)
                result = await analyze_image(image_path, prompt)

                # Get the name of the image without its extension
                image_name = await get_image_name_without_extension(image_path)

                # Store the result in the dictionary with the image name as the key
                ocr_dictionary[int(image_name)] = result

                log_info(f"Image: {image_file} has been processed successfully.")
                log_info("")
            except Exception as e:
                log_error(f"An error occurred while processing {image_file}: {e}")
    
        # Run all tasks concurrently
        await asyncio.gather(*(process_image(each_image) for each_image in all_images))

        sorted_dictionary = await sort_dictionary_by_keys(ocr_dictionary)

        # Append the sorted results to the text file
        for each_value in sorted_dictionary:
            await append_to_file(text_file_path, each_value)

        # Copy the text to clipboard
        await copy_to_clipboard()

    except Exception as e: 
        log_error(f"An error occurred during execution: {e}") 
    

# main function 
async def main():

    if len(sys.argv) > 2:
        log_error("Too many arguments provided. Please provide only one argument for the prompt.")
        return
    elif len(sys.argv) != 2:
        await execute()
    else:
        prompt = sys.argv[1]
        await execute(prompt)
 
if __name__ == "__main__": 
    import time
    start_time = time.perf_counter()
    asyncio.run(main()) 
    end_time = time.perf_counter() - start_time
    log_info(f"Execution time: {end_time:.2f} seconds")


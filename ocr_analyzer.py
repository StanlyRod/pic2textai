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

# # Create logger
rich_logging = logging.getLogger("rich_logger")

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
        rich_logging.info(f"Text appended to {path}") 
    except PermissionError:
        rich_logging.error(f"Permission denied: Unable to open file or the file is currently in use {path}. Please check file permissions.")
    except FileNotFoundError:
        rich_logging.error(f"File not found: {path}. Please ensure the file exists.")
    except Exception as e: 
        rich_logging.error(f"Failed to append to file: {e}") 

 

# encode image to base64
async def encode_image(image_path: str) -> str: 
    try: 
        async with AIOFile(image_path, "rb") as image_file: 
            content = await image_file.read()
        return base64.b64encode(content).decode("utf-8") 
    except Exception as e: 
        rich_logging.error(f"Failed to encode image {image_path}: {e}") 
        return "" 

 

# Asynchronous function to process the OpenAI API request 
async def analyze_image(image_path: str, prompt: str) -> str: 
    try: 
        # call the encode_image function to encode the image to base64
        base64_image = await encode_image(image_path) 

        if not base64_image: 
            return "Failed to encode image" 
        
        response = await client.chat.completions.create( 
            model="gpt-4o", 
            messages=[ 
                { 
                    "role": "user", 
                    "content": [ 
                        {"type": "text", "text": f"{prompt}"}, 
                        { 
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}, 
                        }, 
                    ], 
                } 
            ], 
        ) 

        text_response = response.choices[0].message.content 

        text_response = text_response.encode("utf-8").decode("utf-8", errors="replace") 

        return text_response.replace("�", "'") 
    
    except Exception as e: 
        rich_logging.error(f"Failed to analyze image {image_path}: {e}") 
        return "Failed to analyze image" 
    

# read the text file
async def read_text_file(file_path):
    try:
        async with AIOFile(file_path, 'r') as text_file:
            # Read the content of the file
            content = await text_file.read()
        return content
    except FileNotFoundError:
        rich_logging.error(f"File not found: {file_path}. Please ensure the file exists.")
        return ""
    except PermissionError:
        rich_logging.error(f"Permission denied: Unable to read the file {file_path}. Please check file permissions.")
        return ""
    except Exception as e:
        rich_logging.error(f"An error occurred while reading the file {file_path}: {e}")
        return ""
    

# function to copy text to clipboard
async def copy_to_clipboard():
    # Read the text file
    content = await read_text_file(text_file_path)
    if content:
        # Copy the content to clipboard
        pyperclip.copy(content)
        rich_logging.info("Text copied to clipboard successfully.")
    else:  
        rich_logging.error("No content to copy to clipboard.")
        return


# Function to rename images in the with enumeration
def rename_images_with_enumeration(folder_path: str):
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
            if each_image.endswith(".png"):
                try:
                    # Full path to the old image
                    old_path = os.path.join(folder_path, each_image)

                    # Generate a new name for the image (like: "1.png", "2.png", etc.)
                    new_name = f"{count_images}.png"
                    new_path = os.path.join(folder_path, new_name)

                    # Rename the file in place
                    os.rename(old_path, new_path)

                    # Log the renaming operation
                    rich_logging.info(f"Renamed {each_image} to {new_name}")
                    rich_logging.info("")

                    # Increment count 
                    count_images += 1
                except FileNotFoundError:
                    rich_logging.error(f"File not found: {each_image}. Skipping...")
                except PermissionError:
                    rich_logging.error(f"Permission denied: Unable to rename {each_image}. Skipping...")
                except Exception as e:
                    rich_logging.error(f"An error occurred while renaming {each_image}: {e}")
    except FileNotFoundError as e:
        rich_logging.error(e)
    except PermissionError:
        rich_logging.error(f"Permission denied: Unable to access the folder {folder_path}.")
    except Exception as e:
        rich_logging.error(f"An unexpected error occurred: {e}")


# Extracts the name of the file without its extension from the given file path.
async def get_image_name_without_extension(image_name_path: str) -> str:
    try:
        path = Path(image_name_path)
        return path.stem
    except Exception as e:
        rich_logging.error(f"An error occurred while extracting the file name: {e}")
        return ""
    

async def sort_dictionary_by_keys(input_dict):
    sorted_dict = dict(sorted(input_dict.items()))
    values = sorted_dict.values()
    try:
        return values
        # for each_value in values:
        #     await append_to_file(text_file_path, each_value)
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        return ""


ocr_dictionary = {}


# function to execute the main logic
async def execute(prompt: str = "Extract all the text from this image"):
    try: 
        #=================================================================
        #joining the current directory with the folder
        create_directory = os.path.join(current_directory, "imagesfolder")

        # Create the directory by skipping errors
        os.makedirs(create_directory, exist_ok=True)
        #=================================================================

        images_folder = os.path.join(current_directory, "imagesfolder") 

        # Check if the "imagesfolder" directory exists
        if not os.path.exists(images_folder): 
            rich_logging.error(f"Folder not found: {images_folder}") 
            return # Exit the function if the folder doesn't exist
        
        rename_images_with_enumeration(images_folder)

        # List all image files in the specified folder with extensions .png, .jpeg, or .jpg
        all_images = [each_image for each_image in os.listdir(images_folder) if each_image.lower().endswith((".png", ".jpeg", ".jpg"))]

        # Count the total number of files in the "imagesfolder" directory
        total_images =  len(all_images)

        # Log the total number of images to be analyzed
        rich_logging.info(f"Total images to be analyze: {total_images}")

        #count_images = 0 


        async def process_image(image_file:str):
            try:
                image_path = os.path.join(images_folder, image_file)
                result = await analyze_image(image_path, prompt)

                # Get the name of the image without its extension
                image_name = await get_image_name_without_extension(image_path)

                # Store the result in the dictionary with the image name as the key
                ocr_dictionary[int(image_name)] = result

                rich_logging.info(f" Analyzed image: {image_file}")
            except Exception as e:
                rich_logging.error(f"An error occurred while processing {image_file}: {e}")


        # Create a list of tasks for processing each image
        tasks = []

        # Iterate through each image and create a task for it
        for each_image in all_images:
            tasks.append(process_image(each_image))

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

        sorted_dictionary = await sort_dictionary_by_keys(ocr_dictionary)

        # Append the sorted results to the text file
        for each_value in sorted_dictionary:
            await append_to_file(text_file_path, each_value)

            
        
        # Iterate through each file in the "imagesfolder" directory
        # for each_image in os.listdir(images_folder): 
        #     # Check if the file has a ".png" extension
        #     if each_image.endswith(".png"): 

        #         image_path = os.path.join(images_folder, each_image)
        #         # Analyze the image with the analyze_image function 
        #         result = await analyze_image(image_path, prompt) 

        #         # Get the name of the image without its extension
        #         image_name = await get_image_name_without_extension(image_path)

        #         # Store the result in the dictionary with the image name as the key
        #         ocr_dictionary[int(image_name)] = result


        #         # Append the result to a text file
        #         #await append_to_file(file_path, result) 

        #         # Increment the counter for each processed image
        #         count_images += 1

        #         rich_logging.info(f"Image - {count_images} - analyzed")

        #rich_logging.info(f"A total of {count_images} images has been processed successfully" if count_images > 0 else "No images were analyzed")


        # Copy the text to clipboard
        await copy_to_clipboard()

    except Exception as e: 
        rich_logging.error(f"An error occurred during execution: {e}") 
    

# main function 
async def main():

    if len(sys.argv) > 2:
        rich_logging.error("Too many arguments provided. Please provide only one argument for the prompt.")
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
    rich_logging.info(f"Execution time: {end_time:.2f} seconds")







# cwd = os.getcwd()

# full_path = os.path.join(cwd, "ocr_analyzer.py")













#===========================================================================================================

#============================================================================================================
'''
this code down here work in parallel 
'''
#============================================================================================================


# #Get the current working directory
# current_directory = os.getcwd()

# #Join the current directory with the images folder
# images_folder = os.path.join(current_directory, "imagesfolder")


# #import aiofiles.os as aio_os

# # Function to rename images in the specified folder with enumeration (asynchronous)
# async def rename_images_with_enumeration(folder_path: str):
#     try:
#         # Check if the images folder exists
#         if not await aio_os.path.exists(folder_path):
#             raise FileNotFoundError(f"Folder not found: {folder_path}")

#         # Initialize a counter for renaming images
#         count_images = 1

#         # Iterate through the files in the folder asynchronously

#         entries = await aio_os.scandir(folder_path)
#         for each_image in entries:
#             # Process only files with a ".png" extension
#             if each_image.name.endswith(".png"):
#                 try:
#                     # Full path to the old image
#                     old_path = os.path.join(folder_path, each_image.name)

#                     # Generate a new name for the image (like: "1.png", "2.png", etc.)
#                     new_name = f"{count_images}.png"
#                     new_path = os.path.join(folder_path, new_name)

#                     # Rename the file in place asynchronously
#                     await aio_os.rename(old_path, new_path)

#                     # Log the renaming operation
#                     rich_logging.info(f"Renamed {each_image.name} to {new_name}")
#                     rich_logging.info("")

#                     # Increment count
#                     count_images += 1
#                 except FileNotFoundError:
#                     rich_logging.error(f"File not found: {each_image.name}. Skipping...")
#                 except PermissionError:
#                     rich_logging.error(f"Permission denied: Unable to rename {each_image.name}. Skipping...")
#                 except Exception as e:
#                     rich_logging.error(f"An error occurred while renaming {each_image.name}: {e}")
#     except FileNotFoundError as e:
#         rich_logging.error(e)
#     except PermissionError:
#         rich_logging.error(f"Permission denied: Unable to access the folder {folder_path}.")
#     except Exception as e:
#         rich_logging.error(f"An unexpected error occurred: {e}")

# async def main():
#     # Check if the "imagesfolder" directory exists
#     if not os.path.exists(images_folder):
#         rich_logging.error(f"Folder not found: {images_folder}")
#         return  # Exit the function if the folder doesn't exist

#     # Call the asynchronous function to rename images with enumeration
#     await rename_images_with_enumeration(images_folder)

# if __name__ == "__main__":
#     # Run the main function asynchronously
#     asyncio.run(main()) 


#===========================================================================================================
   
#rename_images_with_enumeration(images_folder)
       

# dictionary = {5: "The apple is red", 3: "The lemon is yellow", 1: "The banana is yellow", 4: "The orange is orange", 2: "The grape is purple"}

# new_sorted = dict(sorted(dictionary.items()))
                  
# print(new_sorted)

# for key in sorted(dictionary.keys()):
#     print(f"{key}: {dictionary[key]}")
from aiofile import AIOFile, Writer  # type: ignore 
import asyncio 
import os 
import base64 
import pyperclip # type: ignore
import logging_module as lm
import sys 
from openai import AsyncOpenAI  # type: ignore 
from pathlib import Path
import text_utils as tu
import time


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

# Rate limiting configuration
IMAGES_PER_SECOND = 20
SEMAPHORE_LIMIT = IMAGES_PER_SECOND
RATE_LIMIT_DELAY = 0.05 / IMAGES_PER_SECOND

# Create semaphore for rate limiting
rate_limiter = asyncio.Semaphore(SEMAPHORE_LIMIT)


# encode image to base64
async def encode_image(image_path: str) -> str: 
    try: 
        async with AIOFile(image_path, "rb") as image_file: 
            content = await image_file.read()
        return base64.b64encode(content).decode("utf-8") 
    except Exception as e: 
        lm.log_error(f"Failed to encode image {image_path}: {e}") 
        return "" 

total_tokens = 0
 
# Asynchronous function to process the OpenAI API request with rate limiting
async def analyze_image(image_path: str, prompt: str) -> str: 
    global total_tokens  # Use the global variable to track total tokens used
    async with rate_limiter:
        try: 
            # Add delay to enforce rate limiting
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
            # call the encode_image function to encode the image to base64
            base64_image = await encode_image(image_path) 

            if not base64_image: 
                return "Failed to encode image" 
            
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg"}.get(ext[1:], "image/png")
            
            response = await client.chat.completions.create( 
                model="gpt-4.1-nano-2025-04-14", 
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

            if hasattr(response, 'usage') and response.usage:
                total_tokens += response.usage.total_tokens

            text_response = response.choices[0].message.content 

            text_response = text_response.encode("utf-8").decode("utf-8", errors="replace") 

            return text_response.replace("�", "'") 
        
        except Exception as e: 
            lm.log_error(f"Failed to analyze image {image_path}: {e}") 
            return "Failed to analyze image" 


SUPPORTED_IMAGE_FORMATS = (".png", ".jpeg", ".jpg")

async def rename_images_with_enumeration(folder_path: str):
    try:
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Create empty list for image files only
        files = []
        
        # Loop through all files in the folder
        for file in os.listdir(folder_path):
            lowercase_filename = file.lower()
            # Check if file has supported image extension
            if lowercase_filename.endswith(SUPPORTED_IMAGE_FORMATS):
                #add image to the list
                files.append(file)

        # Sort files by modification time (oldest to newest)
        files.sort(key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))

        count_images = 1

        for each_image in files:
            try:
                old_path = os.path.join(folder_path, each_image)
                extension = os.path.splitext(each_image)[1].lower()
                new_name = f"{count_images}{extension}"
                new_path = os.path.join(folder_path, new_name)

                os.rename(old_path, new_path)
                lm.log_info(f"Renamed {each_image} → {new_name}")
                count_images += 1

            except FileNotFoundError:
                lm.log_error(f"File not found: {each_image}. Skipping...")
            except PermissionError:
                lm.log_error(f"Permission denied: Unable to rename {each_image}. Skipping...")
            except Exception as e:
                lm.log_error(f"Error renaming {each_image}: {e}")
    except FileNotFoundError as e:
        lm.log_error(str(e))
    except PermissionError:
        lm.log_error(f"Permission denied: Unable to access the folder {folder_path}.")
    except Exception as e:
        lm.log_error(f"Unexpected error: {e}")


# Extracts the name of the file without it's extension from the given file path.
async def get_image_name_without_extension(image_name_path: str) -> str:
    try:
        path = Path(image_name_path)
        return path.stem
    except Exception as e:
        lm.log_error(f"An error occurred while extracting the file name: {e}")
        return ""
    

# Function to sort the dictionary by keys
async def sort_dictionary_by_keys(input_dict):
    sorted_dict = dict(sorted(input_dict.items()))
    values = sorted_dict.values()
    try:
        return values
    except Exception as e:
        lm.log_error(f"An error occurred while writing to the file: {e}")
        return ""


# Rate-limited image processing function
async def process_image_with_rate_limit(image_file: str, images_folder: str, prompt: str, ocr_dictionary: dict):
    """Process a single image with rate limiting"""
    try:
        image_path = os.path.join(images_folder, image_file)
        
        # The rate limiting is handled inside analyze_image function
        result = await analyze_image(image_path, prompt)

        # Get the name of the image without its extension
        image_name = await get_image_name_without_extension(image_path)

        # Store the result in the dictionary with the image name as the key
        ocr_dictionary[int(image_name)] = result

        lm.log_info(f"Image: {image_file} has been processed successfully.")
        lm.log_info("")
        
    except Exception as e:
        lm.log_error(f"An error occurred while processing {image_file}: {e}")


# function to execute the main logic
async def execute(prompt: str = "Extract only all the text from this image"):
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
            lm.log_error(f"Folder not found: {images_folder}") 
            return # Exit the function if the folder doesn't exist
        
        await rename_images_with_enumeration(images_folder)

        # List all image files in the specified folder with extensions .png, .jpeg, or .jpg
        all_images = [each_image for each_image in os.listdir(images_folder) if each_image.lower().endswith((".png", ".jpeg", ".jpg"))]

        # Count the total number of files in the "imagesfolder" directory
        total_images = len(all_images)

        # Log the total number of images to be analyzed
        lm.log_info(f"Total images to be analyzed: {total_images}")
        lm.log_info(f"Processing at {IMAGES_PER_SECOND} images per second")
        lm.log_info("")

        # Record start time for rate limiting monitoring
        start_time = time.perf_counter()
        
        # Create tasks for all images - rate limiting is handled by semaphore
        tasks = [
            process_image_with_rate_limit(image_file, images_folder, prompt, ocr_dictionary)
            for image_file in all_images
        ]
        
        # Run all tasks concurrently with rate limiting
        await asyncio.gather(*tasks)
        
        # Log actual processing time
        actual_time = time.perf_counter() - start_time
        actual_rate = total_images / actual_time if actual_time > 0 else 0
        lm.log_info(f"Actual processing time: {actual_time:.2f} seconds")
        lm.log_info(f"Actual rate: {actual_rate:.2f} images per second")
        lm.log_info("")

        sorted_dictionary = await sort_dictionary_by_keys(ocr_dictionary)

        # Append the sorted results to the text file
        for each_value in sorted_dictionary:
            await tu.append_to_file(text_file_path, each_value)

        lm.log_info(f"Results have been written to {text_file_path} successfully.")
        lm.log_info("")

        # Copy the text to clipboard
        await tu.copy_to_clipboard(text_file_path)

    except Exception as e: 
        lm.log_error(f"An error occurred during execution: {e}") 
    

# main function 
async def main():
    if len(sys.argv) > 2:
        lm.log_error("Too many arguments provided. Please provide only one argument for the prompt.")
        return
    elif len(sys.argv) != 2:
        await execute()
    else:
        prompt = sys.argv[1]
        await execute(prompt)
 
if __name__ == "__main__": 
    start_time = time.perf_counter()
    asyncio.run(main()) 
    end_time = time.perf_counter() - start_time
    lm.log_info(f"Total execution time: {end_time:.2f} seconds")
    lm.log_info(f"Total tokens used: {total_tokens}")
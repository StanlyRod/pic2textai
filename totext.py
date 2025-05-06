from aiofile import AIOFile, Writer  # type: ignore 
import asyncio 
import os 
import base64 
import logging
import pyperclip # type: ignore
from rich import print
from rich.logging import RichHandler
import sys 
from openai import OpenAI  # type: ignore 

# Configure logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S",handlers=[RichHandler()] ) 

# Create logger
rich_logging = logging.getLogger("rich_logger")

# Get the current working directory 
current_directory = os.getcwd() 

# File name
filename = "extractedtext.txt"

# joining the current directory with the filename
file_path = os.path.join(current_directory, filename) 
 
 # get openai api key from environmental variable
openaikey = os.getenv("OPENAIKEY") 

# check for OpenAI API key and raise an exception if the environmental variable is not set
if not openaikey: 
    raise EnvironmentError("OPENAIKEY environment variable not set") 

client = OpenAI(api_key=openaikey) 

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
        
        response = client.chat.completions.create( 
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


async def execute(prompt: str = "Extract all the text from this image"):
    try: 
        #joining the current directory with the folder
        create_directory = os.path.join(current_directory, "imagesfolder")

        # Create the directory by skipping errors
        os.makedirs(create_directory, exist_ok=True)

        images_folder = os.path.join(current_directory, "imagesfolder") 

        # Check if the "imagesfolder" directory exists
        if not os.path.exists(images_folder): 
            rich_logging.error(f"Folder not found: {images_folder}") 
            return # Exit the function if the folder doesn't exist

        # Count the total number of files in the "imagesfolder" directory
        total_images =  len(os.listdir(images_folder))

        # Log the total number of images to be analyzed
        rich_logging.info(f"Total images to be analyze: {total_images}")

        count_images = 0 
        
        # Iterate through each file in the "imagesfolder" directory
        for each_image in os.listdir(images_folder): 
            # Check if the file has a ".png" extension
            if each_image.endswith(".png"): 

                image_path = os.path.join(images_folder, each_image)
                # Analyze the image with the analyze_image function 
                result = await analyze_image(image_path, prompt) 
                # Append the result to a text file
                await append_to_file(file_path, result) 

                # Increment the counter for each processed image
                count_images += 1

                rich_logging.info(f"Image - {count_images} - analyzed")

        rich_logging.info(f"A total of {count_images} images has been processed successfully" if count_images > 0 else "No images were analyzed")

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
    asyncio.run(main()) 



# async def read_text_file(file_path):
#     try:
#         async with AIOFile(file_path, 'r') as text_file:
#             # Read the content of the file
#             content = await text_file.read()
#         return content
#     except FileNotFoundError:
#         rich_logging.error(f"File not found: {file_path}. Please ensure the file exists.")
#         return ""
#     except PermissionError:
#         rich_logging.error(f"Permission denied: Unable to read the file {file_path}. Please check file permissions.")
#         return ""
#     except Exception as e:
#         rich_logging.error(f"An error occurred while reading the file {file_path}: {e}")
#         return ""


# async def main():
#     # Read the text file
#     content = await read_text_file(file_path)
    
#     # Check if content is not empty
#     if content:
#         # Copy the content to clipboard
#         pyperclip.copy(content)
#         rich_logging.info("Text copied to clipboard successfully.")
#     else:
#         rich_logging.error("No content to copy to clipboard.")
#         return
#     # Print the content to the console
#     print(content)
#     # Print a message indicating that the content has been copied
#     print("Text copied to clipboard successfully.")
#     # Print a message indicating that the content has been printed
#     print("Text printed to console successfully.")
#     # Print a message indicating that the content has been printed

# if __name__ == "__main__":
#     asyncio.run(main())
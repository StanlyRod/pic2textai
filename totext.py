from aiofile import AIOFile, Writer  # type: ignore 
import asyncio 
import os 
import base64 
import logging 
from openai import OpenAI  # type: ignore 

# Configure logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") 

# Get the current working directory 
current_directory = os.getcwd() 

# File paths 
filename = "extractedText.txt" 

# joining the current directory with the filename
file_path = os.path.join(current_directory, filename) 
 
# Check for OpenAI API key 
openaikey = os.getenv("OPENAIKEY") 

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

        logging.info(f"Text appended to {path}") 
    except Exception as e: 
        logging.error(f"Failed to append to file: {e}") 

 

# encode an image to base64 
async def encode_image(image_path: str) -> str: 
    try: 
        async with AIOFile(image_path, "rb") as image_file: 
            content = await image_file.read() 

        return base64.b64encode(content).decode("utf-8") 
    except Exception as e: 
        logging.error(f"Failed to encode image {image_path}: {e}") 
        return "" 

 

# Asynchronous function to process the OpenAI API request 
async def analyze_image(image_path:str, prompt:str) -> str: 
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
        logging.error(f"Failed to analyze image {image_path}: {e}") 
        return "Failed to analyze image" 

 

# main function 
async def main(): 
    try: 
        #joining the current directory with the folder
        create_directory = os.path.join(current_directory, "imagesfolder")

        # Create the directory by skipping errors
        os.makedirs(create_directory, exist_ok=True)

        images_folder = os.path.join(current_directory, "imagesfolder") 

        # Check if the "imagesfolder" directory exists
        if not os.path.exists(images_folder): 
            logging.error(f"Folder not found: {images_folder}") 
            return # Exit the function if the folder doesn't exist

        # Count the total number of files in the "imagesfolder" directory
        total_images =  len(os.listdir(images_folder))

        # Log the total number of images to be analyzed
        logging.info(f"Total images to be analyze: {total_images}")

        count_images = 0 
        
        # iterate through each file in the "imagesfolder" directory
        for each_image in os.listdir(images_folder): 
            # Check if the file has a ".png" extension
            if each_image.endswith(".png"): 

                image_path = os.path.join(images_folder, each_image)
                # Analyze the image with the analyze_image function 
                result = await analyze_image(image_path, "Extract all the text from this images then analyze the info and create a study note") 
                # Append the result to a text file
                await append_to_file(file_path, result) 

                # Increment the counter for each processed images
                count_images += 1 

                logging.info(f"Image - {count_images}")

        logging.info(f"A total of {count_images} images has been processed succesfully") 
    except Exception as e: 
        logging.error(f"An error occurred during execution: {e}") 

 
if __name__ == "__main__": 
    asyncio.run(main()) 



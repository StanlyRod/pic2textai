from aiofile import AIOFile, Writer # type: ignore
import asyncio
import os
import sys

# Get the current working directory
current_directory = os.getcwd()

# file name
filename = "extractedText.txt"

# full file path
file_path = os.path.join(current_directory, filename)

# function to append to a text file
async def append_to_file(path:str , text:str):
   
    try:
        # open file in append mode
        async with AIOFile(path, 'a') as afp:  
            writer = Writer(afp)

            # append the text with a newline
            await writer(f"{text}\n")  

            # Ensure data is flushed to disk
            await afp.fsync()  

        print(f"Text appended to {path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# async def main():
#     await append_to_file(file_path, "C# is back-end programing and game development")
#     await append_to_file(file_path, "JavaScript is for front-end web development")

# asyncio.run(main())

# Example usage (to be run in an async context):
# import asyncio
# asyncio.run(append_to_file("example.txt", "This is the appended text"))


import base64
from openai import OpenAI # type: ignore

openaikey = os.environ["OPENAIKEY"]

client = OpenAI(api_key=openaikey)


# full file path
# fileimage_path = os.path.join(current_directory, filename)


# Asynchronous function to encode the image
async def encode_image(image_path):
    async with AIOFile(image_path, "rb") as image_file:
        content = await image_file.read()
        return base64.b64encode(content).decode("utf-8")


# Asynchronous function to process the OpenAI API request
async def analyze_image(image_path):
    # Encode the image to base64
    base64_image = await encode_image(image_path)
    
    # Make an asynchronous API call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the text from this image"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )
    
    # Return the response
    text_response = response.choices[0].message.content

    #the text is handled as UTF-8
    text_response = text_response.encode("utf-8").decode("utf-8", errors="replace")

    if "�" in text_response:
        text_response.replace("�","'")

    return text_response



# Run the asynchronous function
async def main():

    midnight_folder = os.path.join(current_directory, "midnight")

    count_images = 0
    for each_image in os.listdir(midnight_folder):
        if each_image.endswith(".png"):

            result = await analyze_image(midnight_folder + "\\"+ each_image)
            await append_to_file(file_path, result)

            count_images += 1
    
    print(count_images)



# Start the event loop
asyncio.run(main())
from aiofile import AIOFile, Writer # type: ignore
import asyncio
import os

# Get the current working directory
current_directory = os.getcwd()

# file name
filename = "extractedText.txt"

# full file path
file_path = os.path.join(current_directory, filename)

async def append_to_file(path:str , text:str):
   
    try:
        async with AIOFile(path, 'a') as afp:  # Open file in append mode
            writer = Writer(afp)
            await writer(f"{text}\n")  # Append the text with a newline
            await afp.fsync()  # Ensure data is flushed to disk
        print(f"Text appended to {path}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def main():
    await append_to_file(file_path, "C# is back-end programing and game development")
    await append_to_file(file_path, "JavaScript is for front-end web development")

asyncio.run(main())

# Example usage (to be run in an async context):
# import asyncio
# asyncio.run(append_to_file("example.txt", "This is the appended text"))

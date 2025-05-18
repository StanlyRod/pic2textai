import logging
from rich import print
from rich.logging import RichHandler
from aiofile import AIOFile, Writer
import pyperclip


# function to append text to a text file 
async def append_to_file(path: str, text: str): 
    try: 
        async with AIOFile(path, "a") as afp: 
            writer = Writer(afp) 
            await writer(f"{text}\n") 
            await afp.fsync()
    except PermissionError:
        log_error(f"Permission denied: Unable to open file or the file is currently in use {path}. Please check file permissions.")
    except FileNotFoundError:
        log_error(f"File not found: {path}. Please ensure the file exists.")
    except Exception as e: 
        log_error(f"Failed to append to file: {e}") 


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
async def copy_to_clipboard(text_file_path):
    # Read the text file
    content = await read_text_file(text_file_path)
    if content:
        # Copy the content to clipboard
        pyperclip.copy(content)
        log_info("Text copied to clipboard successfully.")
    else:  
        log_error("No content to copy to clipboard.")
        return








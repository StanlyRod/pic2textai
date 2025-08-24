# OCR Analyzer

A powerful Python script for extracting text from images using OpenAI's GPT-4 Vision API.

This project is specifically designed for users who want to extract text from:

* **Websites and digital platforms that disable copy-paste functionality**
* **E-books or online readers like Amazon Kindle**, where copying text is not allowed

The Python script processes multiple screenshots or image files concurrently with built-in rate limiting and flexible output options. It's ideal for digitizing hard-to-access text for study, research, or offline reference.




## ⚡Features

- **Batch Image Processing**: Process multiple images in a folder simultaneously
- **Rate Limiting**: Built-in rate limiting (10 images per second) to respect API limits
- **Grayscale Conversion**: Optional image preprocessing to grayscale for better OCR results
- **Custom Prompts**: Use custom prompts for specialized text extraction
- **Auto-renaming**: Automatically renames images with enumeration for consistent processing
- **Rich Logging**: Beautiful console output with timestamps and colors
- **Clipboard Integration**: Automatically copies extracted text to clipboard
- **File Output**: Saves all extracted text to a structured text file

## 📦 Requirements

- Python 3.13+
- OpenAI API key
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/StanlyRod/pic2textai.git
cd pic2textai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:

### Windows
**Command Prompt:**
```cmd
set OPENAIKEY=your-openai-api-key-here
```

**PowerShell:**
```powershell
$env:OPENAIKEY="your-openai-api-key-here"
```

**Permanent (System Environment Variables):**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables" click "New"
4. Variable name: `OPENAIKEY`
5. Variable value: `your-openai-api-key-here`
6. Click OK

### Linux/Ubuntu
**Temporary (current session):**
```bash
export OPENAIKEY="your-openai-api-key-here"
```

**Permanent (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export OPENAIKEY="your-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### macOS
**Temporary (current session):**
```bash
export OPENAIKEY="your-openai-api-key-here"
```

**Permanent (add to ~/.zshrc or ~/.bash_profile):**
```bash
echo 'export OPENAIKEY="your-openai-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Note:** Replace `your-openai-api-key-here` with your actual OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## 📁 File Structure

```
pic2textai/
├── ocr_analyzer.py      # Main application file
├── logging_module.py    # Rich logging configuration
├── text_utils.py        # Text file operations and clipboard utilities
├── requirements.txt     # Python dependencies
├── imagesfolder/        # Directory for input images (must be created manually)
└── extractedtext.txt    # Output file (auto-created)
```

## 🧪 Usage

### Basic Usage

**Important:** Create an `imagesfolder/` directory in your project root and place your images there before running the script.

```bash
# Create the images folder
mkdir imagesfolder

# Add your images to the imagesfolder directory
# Then run the script:

# Process images with default prompt
python ocr_analyzer.py

# Process images with custom prompt
python ocr_analyzer.py "Extract all text including numbers and symbols"

# Convert images to grayscale then process with default prompt
python ocr_analyzer.py true

# Convert to grayscale and use custom prompt
python ocr_analyzer.py "Extract only the main text content" true
```

### Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)

### Command Line Arguments

| Arguments | Description | Example |
|-----------|-------------|---------|
| None | Uses default prompt | `python ocr_analyzer.py` |
| `[prompt]` | Custom extraction prompt | `python ocr_analyzer.py "Extract headers only"` |
| `true` | Converts to grayscale + default prompt | `python ocr_analyzer.py true` |
| `[prompt] true` | Custom prompt + grayscale conversion | `python ocr_analyzer.py "Extract text" true` |

## How It Works

1. **Image Preparation**: 
   - Requires `imagesfolder/` directory to exist (must be created manually)
   - Scans for supported image formats
   - Optionally converts images to grayscale
   - Renames images in ascending sequential order by modification time (1.png, 2.jpg, etc.)

2. **Processing**:
   - Encodes images to base64 format
   - Sends concurrent requests to OpenAI GPT-4 Vision API
   - Applies rate limiting (30 images/second with semaphore)
   - Extracts text using specified prompt

3. **Output**:
   - Sorts results by image number
   - Saves all extracted text to `extractedtext.txt`
   - Copies content to system clipboard
   - Provides detailed logging of the process

## Configuration

### Rate Limiting
```python
IMAGES_PER_SECOND = 10          # Maximum processing rate
SEMAPHORE_LIMIT = 10            # Concurrent request limit
RATE_LIMIT_DELAY = 0.10/10      # Delay between requests
```

### OpenAI Model
Currently uses: `gpt-4.1-nano-2025-04-14`

## File Descriptions

### `ocr_analyzer.py`
Main application containing:
- Image encoding and API communication
- Concurrent processing with asyncio
- Rate limiting implementation
- Command line argument parsing
- File management and sequential image renaming by modification time
- Grayscale image conversion functionality

### `logging_module.py`
Logging configuration using Rich library:
- Colored console output
- Timestamp formatting
- Info and error logging functions

### `text_utils.py`
Utility functions for text operations:
- Asynchronous file writing
- Text file reading
- Clipboard integration
- Error handling for file operations

## Error Handling

The application includes comprehensive error handling for:
- Missing OpenAI API key
- File permission errors
- Network connectivity issues
- Invalid image formats
- API rate limiting
- File system errors

## Performance

- **Concurrent Processing**: Uses asyncio for simultaneous image processing
- **Rate Limiting**: Respects API limits while maximizing throughput
- **Memory Efficient**: Processes images individually without loading all into memory
- **Progress Tracking**: Real-time logging of processing status

## Output Example

```
2025-01-15 10:30:45 - INFO - Total images to be analyzed: 5
2025-01-15 10:30:45 - INFO - Processing at 10 images per second
2025-01-15 10:30:45 - INFO - Renamed IMG_001.jpg → 1.jpg
2025-01-15 10:30:45 - INFO - Renamed IMG_002.jpg → 2.jpg
2025-01-15 10:30:46 - INFO - Image: 1.jpg has been processed successfully.
2025-01-15 10:30:47 - INFO - Actual processing time: 2.15 seconds
2025-01-15 10:30:47 - INFO - Actual rate: 2.33 images per second
2025-01-15 10:30:47 - INFO - Results have been written to extractedtext.txt successfully.
2025-01-15 10:30:47 - INFO - Text copied to clipboard successfully.
2025-01-15 10:30:47 - INFO - Total execution time: 2.18 seconds
2025-01-15 10:30:47 - INFO - Total tokens used: 1250
```

## 🧰 Troubleshooting

### Common Issues

1. **"OPENAIKEY environment variable not set"**
   - Ensure your OpenAI API key is properly set as an environment variable

2. **"Folder not found: imagesfolder"**
   - Create the `imagesfolder/` directory manually in your project root
   - Add your images to this directory before running the script

3. **Permission Errors**
   - Check file permissions for the working directory
   - Ensure images aren't open in other applications

4. **No images found**
   - Verify images are in the `imagesfolder/` directory
   - Check that image formats are supported (.png, .jpg, .jpeg)

5. **API Errors**
   - Verify OpenAI API key is valid and has sufficient credits
   - Check internet connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request



## Dependencies

See `requirements.txt` for complete list. Key dependencies:
- `openai`: OpenAI API client
- `aiofile`: Asynchronous file operations
- `rich`: Enhanced console output
- `pillow`: Image processing
- `pyperclip`: Clipboard operations


## 📄 License

This project is licensed under the [MIT License](LICENSE).
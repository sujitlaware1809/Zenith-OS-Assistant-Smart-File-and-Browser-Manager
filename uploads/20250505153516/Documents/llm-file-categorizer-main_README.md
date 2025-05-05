# LLM File Categorizer

The LLM File Categorizer is a Python script that utilizes the Anthropic API and the Claude models (Haiku and Opus) to automatically categorize and sort files in a given folder. It uses the Haiku model to process various types of files, including text files, images, and other file types, and generates descriptions for each file. The Opus model is then used to suggest categories based on the file descriptions. Finally, the script organizes the files into appropriate folders based on their assigned categories.

## Features

- Automatically categorizes and sorts files in a specified folder
- Supports text files, images, and other file types
- Utilizes the Anthropic API and the Claude models (Haiku and Opus) for intelligent file categorization
- Generates file descriptions using the Haiku model
- Suggests categories based on file descriptions using the Opus model
- Creates category folders and moves files into their respective folders
- Provides colored output for better visibility and clarity

## Requirements

- Python 3.x
- Anthropic API key
- Required Python libraries:
  - `anthropic`
  - `python-dotenv`
  - `termcolor`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/llm-file-categorizer.git
   ```

2. Navigate to the project directory:
   ```
   cd llm-file-categorizer
   ```

3. Install the required libraries:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Anthropic API key:
   - Sign up for an Anthropic API account at [https://www.anthropic.com](https://www.anthropic.com)
   - Obtain your API key
   - Create a `.env` file in the project directory and add the following line:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```
     Replace `your_api_key_here` with your actual Anthropic API key.

## Usage

1. Place the files you want to categorize in a folder.

2. Run the `categorizer.py` script:
   ```
   python categorizer.py
   ```

3. When prompted, enter the path to the folder containing the files you want to categorize.

4. The script will process each file, generate descriptions, suggest categories, create category folders, and move the files into their respective folders.

5. Once the categorization is complete, you will see a message indicating that the process is finished.

## How It Works

1. The script retrieves the list of files in the specified folder.

2. For each file, it determines the file type (text, image, or other) based on the MIME type.

3. Depending on the file type, it sends the file content or image data to the Haiku model using the Anthropic API to generate a description of the file.

4. After obtaining descriptions for all files, it sends the descriptions to the Opus model to suggest category names.

5. It creates folders for each suggested category in the specified folder.

6. For each file, it sends the file description and available categories to the Haiku model to determine the most appropriate category.

7. It moves each file into its corresponding category folder.

## Acknowledgements

This project was inspired by a [tweet](https://twitter.com/alexalbert__/status/1769417059794870541) by Alex Albert, a prompt engineer at Anthropic. Although Alex didn't open-source his script, this project aims to reproduce the functionality based on the description provided in the tweet.

## License

This project is licensed under the [MIT License](LICENSE).

## Disclaimer

Please note that this script relies on the Anthropic API and may consume API credits. Use it responsibly and within the limits of your API plan. The script assumes you have the necessary permissions and rights to access and modify the files in the specified folder.
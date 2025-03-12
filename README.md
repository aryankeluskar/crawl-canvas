# Canvas AI Learning Resource Agent

This agent helps students find relevant learning resources for their questions by connecting to Canvas LMS and using Gemini AI to analyze their queries.

## Features

- Analyzes student queries to identify the most relevant course
- Processes images of educational content to understand concepts
- Finds the most appropriate modules within that course
- Retrieves and ranks learning resources (videos, PDFs, assignments, etc.)
- Uses Google's Gemini 2.0 Flash for fast, accurate natural language understanding

## Setup

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure Environment Variables**

Create a `.env` file in the root directory with your Canvas API key:

```
CANVAS_API_KEY=your_canvas_api_key_here
```

To get your Canvas API key:
1. Log in to Canvas
2. Go to Account > Settings
3. Scroll down to "Approved Integrations"
4. Click "New Access Token"
5. Follow the prompts to generate a token

## Usage

### Command-Line Interface

The agent comes with a convenient command-line interface:

```bash
# Ask a text question
python canvas_cli.py --query "I don't understand what orthogonalization of matrices mean"

# Analyze an image
python canvas_cli.py --image "path/to/your/image.png"

# Analyze an image with additional context
python canvas_cli.py --query "Explain this concept" --image "path/to/your/image.png"

# Run with detailed output
python canvas_cli.py --query "How do process scheduling algorithms work?" --verbose

# Run test cases
python canvas_cli.py --test
```

### Python API

You can also use the agent directly in your Python code:

```python
from canvas import find_resources

# Find resources for a text question
resources = find_resources("I don't understand what orthogonalization of matrices mean")

# Find resources for an image
resources = find_resources("", image_path="path/to/your/image.png")

# Find resources for an image with context
resources = find_resources("Help me understand this", image_path="path/to/your/image.png")

# Process and display the resources
for resource in resources:
    print(f"Title: {resource.get('title')}")
    print(f"URL: {resource.get('url')}")
    print(f"Relevance: {resource.get('relevance_score')}")
```

## Testing

The module includes a `test_agent()` function that tests the agent with sample queries from various subjects:

```python
from canvas import test_agent

test_agent()
```

## How It Works

1. If an image is provided, it's analyzed by Gemini Vision to extract the educational concept shown
2. The agent retrieves all courses from your Canvas account
3. Gemini AI analyzes the query (text and/or image) to determine the most relevant course
4. It then fetches all modules from that course
5. Gemini AI analyzes which modules are most likely to contain relevant information
6. The agent retrieves items from those modules
7. Gemini AI ranks the resources by relevance to the student's query
8. The agent returns a sorted list of the most helpful resources 
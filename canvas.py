import http
import sys
import time
from dotenv import load_dotenv
import os
import json
import requests
import base64
import google.generativeai as genai
from pathlib import Path
import mimetypes

from fastapi import FastAPI, Response, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

load_dotenv()



def get_courses():
    # canvas.asu.edu/api/v1/users/911835/courses
    url = "https://canvas.asu.edu/api/v1/courses?page=1&per_page=100"
    headers = {
        "Authorization": f"Bearer {os.getenv('CANVAS_API_KEY')}"
    }
    courses = requests.get(url, headers=headers)
    courses = courses.json()

    out = {}

    for course in courses:
        if "id" in course and "name" in course:
            out.update({
                course["name"]: course["id"]
            })

    with open("courses.json", "w") as f:
        json.dump(out, f)

    return out

def get_modules(course_id):
    url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/modules"
    headers = {
        "Authorization": f"Bearer {os.getenv('CANVAS_API_KEY')}"
    }
    modules = requests.get(url, headers=headers)

    modules = modules.json()

    with open("modules.json", "w") as f:
        json.dump(modules, f)

    return modules

def get_module_items(course_id, module_id):
    """Get items within a specific module"""
    url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/modules/{module_id}/items?per_page=100"
    headers = {
        "Authorization": f"Bearer {os.getenv('CANVAS_API_KEY')}"
    }
    response = requests.get(url, headers=headers)
    items = response.json()
    
    return items

def get_file_url(course_id, file_id):
    """Get the download URL for a file"""
    url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/files/{file_id}"
    headers = {
        "Authorization": f"Bearer {os.getenv('CANVAS_API_KEY')}"
    }
    response = requests.get(url, headers=headers)
    file_data = response.json()
    
    if 'url' in file_data:
        return file_data['url']
    return None

def encode_image_to_base64(image_path):
    """Encode an image to base64 for use with Gemini"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        # Default to png if can't determine type
        mime_type = "image/png"
    
    return encoded_string, mime_type

def analyze_image_with_gemini(image_path):
    """
    Use Gemini to analyze an image and extract the learning concept
    Returns a description of the concept in the image
    """
    # Initialize Gemini
    genai.configure(api_key="AIzaSyAkgIwBlXvh67IuCVvi0ZNvtjQDcB-RyVg")
    
    # Create a model instance for multimodal generation
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Encode image
    image_data, mime_type = encode_image_to_base64(image_path)
    
    # Create the prompt for image analysis
    prompt = """
    This is an educational image. Please analyze it and extract the main learning concept 
    or topic being illustrated. Describe what subject area this relates to and any key 
    terminology visible in the image. Give your response as a detailed query that I could
    use to find learning resources about this topic.
    """
    
    # Prepare the image for the API
    image_parts = [
        {
            "mime_type": mime_type,
            "data": image_data
        }
    ]
    
    # Generate content with the image
    response = model.generate_content([prompt, *image_parts])
    
    # Extract the query from the response
    return response.text

def analyze_query_with_gemini(query, courses, course_modules=None):
    """
    Use Gemini to analyze the student's query and determine relevant course and modules
    Returns a dict with course_id, module_ids, and reasoning
    """
    # Initialize Gemini
    genai.configure(api_key="AIzaSyAkgIwBlXvh67IuCVvi0ZNvtjQDcB-RyVg")
    
    # Create a model instance
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Format the courses as a list for the prompt
    courses_list = "\n".join([f"- {name}" for name, id in courses.items()])
    
    # Create the initial prompt to identify the course
    if course_modules is None:
        # First stage: identify the correct course
        prompt = f"""
        You are an AI assistant for educational content. A student has the following question:
        
        "{query}"
        
        Based on this question, which of the following courses is the student most likely referring to? 
        Provide your answer as a JSON object with the fields: 
        - course_name: The name of the most relevant course
        - confidence: A score from 0-1 indicating your confidence
        - reasoning: A brief explanation of why you chose this course
        
        Available courses:
        {courses_list}
        """
        
        response = model.generate_content(prompt)
        try:
            # Parse the result to get the course
            result = json.loads(response.text)
            return result
        except:
            # Fallback if the response isn't proper JSON
            print(f"Error parsing Gemini response: {response.text}")
            # Make a best guess based on the response text
            for course_name in courses:
                if course_name.lower() in response.text.lower():
                    return {
                        "course_name": course_name,
                        "confidence": 0.7,
                        "reasoning": "Extracted from response"
                    }
            # Default to first course if no match
            first_course = list(courses.keys())[0]
            return {
                "course_name": first_course,
                "confidence": 0.5,
                "reasoning": "Default selection"
            }
    else:
        # Second stage: identify relevant modules in the course
        modules_list = "\n".join([f"- {module['name']}" for module in course_modules])
        
        prompt = f"""
        You are an AI assistant for educational content. A student has the following question:
        
        "{query}"
        
        Based on this question, which of the following modules in the course are most relevant?
        Return a JSON object with:
        - module_names: An array of names of the most relevant modules (maximum 3)
        - relevance_explanations: Brief explanation for each module's relevance
        
        Available modules:
        {modules_list}
        """
        
        response = model.generate_content(prompt)
        try:
            # Parse the result to get the modules
            result = json.loads(response.text)
            return result
        except:
            # Fallback if the response isn't proper JSON
            print(f"Error parsing Gemini response: {response.text}")
            # Make a best guess based on the response text
            relevant_modules = []
            for module in course_modules:
                if module['name'].lower() in response.text.lower():
                    relevant_modules.append(module['name'])
            
            if not relevant_modules and course_modules:
                # Default to first module if no match
                relevant_modules = [course_modules[0]['name']]
                
            return {
                "module_names": relevant_modules[:3],
                "relevance_explanations": ["Extracted from response"] * len(relevant_modules[:3])
            }

def analyze_resource_relevance(query, resource_items, course_name, module_name):
    """
    Use Gemini to analyze which resources are most relevant to the student's query
    """
    # Initialize Gemini
    genai.configure(api_key="AIzaSyAkgIwBlXvh67IuCVvi0ZNvtjQDcB-RyVg")
    
    # Create a model instance
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Format the resources as a list for the prompt
    resources_list = "\n".join([f"- {item.get('title', 'Untitled')} (Type: {item.get('type', 'Unknown')})" 
                               for item in resource_items])
    
    prompt = f"""
    You are an AI assistant for educational content. A student has the following question:
    
    "{query}"
    
    This question relates to the course "{course_name}" in the module "{module_name}".
    
    Based on this question, which of the following resources would be most helpful to the student?
    Return a JSON object with:
    - resource_indices: An array of indices (0-based) of the most relevant resources (maximum 5)
    - relevance_scores: An array of relevance scores (0-1) corresponding to each resource
    - reasoning: Brief explanation of why these resources are relevant
    
    Available resources:
    {resources_list}
    """
    
    response = model.generate_content(prompt)
    try:
        # Parse the result to get the relevant resources
        result = json.loads(response.text)
        return result
    except:
        # Fallback if the response isn't proper JSON
        print(f"Error parsing Gemini response: {response.text}")
        # Default to returning first 3 resources
        return {
            "resource_indices": list(range(min(3, len(resource_items)))),
            "relevance_scores": [0.8] * min(3, len(resource_items)),
            "reasoning": "Default selection based on availability"
        }

@app.get("/")
async def root():
    """Root endpoint for the API"""
    return {"message": "Canvas Resource API is running. Use /resources endpoint to find resources."}

@app.get("/resources")
async def resources_endpoint(query: str = Query(..., description="Learning query to search for"), 
                     image_path: str = Query(None, description="Optional path to image for analysis")):
    """API endpoint to find resources based on a student query or image"""
    return find_resources(query, image_path)

def find_resources(query, image_path=None):
    """
    Main function to find resources based on a student query or image
    Returns a list of relevant resources
    """
    # If an image is provided, analyze it to get a query
    if image_path and os.path.exists(image_path):
        print(f"Analyzing image: {image_path}")
        image_query = analyze_image_with_gemini(image_path)
        # Combine the original query with the image analysis
        if query:
            query = f"{query} - {image_query}"
        else:
            query = image_query
        print(f"Image analysis result: {query}")
    
    # Step 1: Get all courses
    courses = get_courses()
    if not courses:
        return [{"error": "No courses found", "details": "Please check your Canvas API configuration"}]
    
    # Step 2: Analyze the query to identify the relevant course
    course_analysis = analyze_query_with_gemini(query, courses)
    course_name = course_analysis.get("course_name")
    
    if course_name not in courses:
        # If the exact course name wasn't found, try to find a partial match
        for name in courses:
            if course_name.lower() in name.lower() or name.lower() in course_name.lower():
                course_name = name
                break
        
        # If still not found, default to the first course
        if course_name not in courses:
            course_name = list(courses.keys())[0]
    
    course_id = courses[course_name]
    
    # Step 3: Get modules for the identified course
    modules = get_modules(course_id)
    if not modules:
        return [{"error": "No modules found", "course": course_name}]
    
    # Step 4: Analyze which modules are most relevant
    module_analysis = analyze_query_with_gemini(query, courses, modules)
    relevant_module_names = module_analysis.get("module_names", [])
    
    # Map module names to IDs
    relevant_modules = []
    for module in modules:
        if module["name"] in relevant_module_names:
            relevant_modules.append(module)
        # If we can't find exact matches, include modules that contain the query keywords
        elif any(keyword.lower() in module["name"].lower() 
                for keyword in query.lower().split() if len(keyword) > 3):
            relevant_modules.append(module)
    
    # If no relevant modules found, include the first few modules
    if not relevant_modules and modules:
        relevant_modules = modules[:2]
    
    # Step 5: Get items from relevant modules and filter for resources
    all_relevant_resources = []
    
    for module in relevant_modules:
        module_id = module["id"]
        module_name = module["name"]
        
        # Get all items in this module
        items = get_module_items(course_id, module_id)
        
        if not items:
            continue
        
        # Analyze which resources are most relevant within this module
        resource_analysis = analyze_resource_relevance(query, items, course_name, module_name)
        relevant_indices = resource_analysis.get("resource_indices", [])
        relevance_scores = resource_analysis.get("relevance_scores", [])
        
        # Add the relevant resources to our results
        for idx_pos, idx in enumerate(relevant_indices):
            if idx < len(items):
                item = items[idx]
                # Format the resource for the response
                resource = {
                    "title": item.get("title", "Untitled Resource"),
                    "type": item.get("type", "Unknown"),
                    "url": item.get("html_url", ""),
                    "course": course_name,
                    "module": module_name,
                    "relevance_score": relevance_scores[idx_pos] if idx_pos < len(relevance_scores) else 0.5
                }
                
                # For file resources, get the actual file URL
                if item.get("type") == "File" and "content_id" in item:
                    file_url = get_file_url(course_id, item["content_id"])
                    if file_url:
                        resource["url"] = file_url
                
                all_relevant_resources.append(resource)
    
    # Sort resources by relevance score (descending)
    all_relevant_resources.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # Return results, or an error if none found
    if all_relevant_resources:
        # save resources to a json file
        with open(f"resources_{query}.json", "w") as f:
            json.dump(all_relevant_resources, f)

        return all_relevant_resources
    else:
        return [{"error": "No relevant resources found", "query": query, "course": course_name}]

def test_agent():
    """Test the agent with various prompts"""
    # Text-based queries
    text_test_prompts = [
        "I don't understand what orthogonalization of matrices mean",
        "How do process scheduling algorithms work in operating systems?",
        "Can someone explain Java inheritance and polymorphism?"
    ]
    
    print("\n\n=== TESTING TEXT-BASED QUERIES ===")
    for prompt in text_test_prompts:
        print(f"\n\nTesting prompt: {prompt}")
        print("-" * 50)
        
        resources = find_resources(prompt)
        print(f"Found {len(resources)} resources:")
        
        for i, resource in enumerate(resources):
            print(f"\n{i+1}. {resource.get('title', 'Untitled')}")
            print(f"   Type: {resource.get('type', 'Unknown')}")
            print(f"   URL: {resource.get('url', 'No URL')}")
            print(f"   Course: {resource.get('course', 'Unknown')}")
            print(f"   Module: {resource.get('module', 'Unknown')}")
            print(f"   Relevance: {resource.get('relevance_score', 0):.2f}")
    
    # Image-based queries
    print("\n\n=== TESTING IMAGE-BASED QUERIES ===")
    image_paths = [
        '/Users/aryank/Developer/HiveMind/assets/orthogonal.png',
        '/Users/aryank/Developer/HiveMind/assets/scalar.png'
    ]
    
    for image_path in image_paths:
        print(f"\n\nTesting image: {image_path}")
        print("-" * 50)
        
        resources = find_resources("", image_path=image_path)
        print(f"Found {len(resources)} resources:")
        
        for i, resource in enumerate(resources):
            print(f"\n{i+1}. {resource.get('title', 'Untitled')}")
            print(f"   Type: {resource.get('type', 'Unknown')}")
            print(f"   URL: {resource.get('url', 'No URL')}")
            print(f"   Course: {resource.get('course', 'Unknown')}")
            print(f"   Module: {resource.get('module', 'Unknown')}")
            print(f"   Relevance: {resource.get('relevance_score', 0):.2f}")

def run_cli_mode():
    """Run in command-line mode with query from command line arguments"""
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"Processing query: {query}")
        results = find_resources(query)
        print(f"Found {len(results)} resources:")
        for i, resource in enumerate(results):
            print(f"\n{i+1}. {resource.get('title', 'Untitled')}")
            print(f"   Type: {resource.get('type', 'Unknown')}")
            print(f"   URL: {resource.get('url', 'No URL')}")
            print(f"   Course: {resource.get('course', 'Unknown')}")
            print(f"   Module: {resource.get('module', 'Unknown')}")
            print(f"   Relevance: {resource.get('relevance_score', 0):.2f}")

if __name__ == "__main__":
    # Check if the script is being run in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_agent()
    # Check if running in CLI mode (has arguments but not --test)
    elif len(sys.argv) > 1:
        run_cli_mode()
    # Otherwise, run as a web server
    else:
        print("Starting FastAPI server at http://0.0.0.0:8000")
        print("Use Ctrl+C to stop the server")
        # For reload to work properly, pass as import string when reload=True
        if os.getenv("RELOAD", "False").lower() == "true":
            # This method requires the file to be in a proper package
            uvicorn.run("canvas:app", host="0.0.0.0", port=8000, reload=True)
        else:
            # This method works for direct app reference but doesn't support reload
            uvicorn.run(app, host="0.0.0.0", port=8000)
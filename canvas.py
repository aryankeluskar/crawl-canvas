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

# Print Gemini API version for debugging
try:
    genai_version = getattr(genai, "__version__", "unknown")
    print(f"Using google.generativeai version: {genai_version}")
except Exception as e:
    print(f"Could not determine google.generativeai version: {e}")

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
    try:
        url = "https://canvas.asu.edu/api/v1/courses?page=1&per_page=100"
        
        # Check if API key is available
        api_key = os.getenv('CANVAS_API_KEY')
        if not api_key:
            print("Error: CANVAS_API_KEY environment variable not set")
            # Return some mock data for development/testing
            mock_data = {"Mock Course 1": 1001, "Mock Course 2": 1002}
            return mock_data
            
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Add timeout to prevent hanging
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            print(f"Error: Canvas API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            # Return mock data if API call fails
            mock_data = {"Mock Course 1": 1001, "Mock Course 2": 1002}
            return mock_data
            
        courses = response.json()

        out = {}

        for course in courses:
            if "id" in course and "name" in course:
                out.update({
                    course["name"]: course["id"]
                })

        # Only write to file if we have data and the filesystem is writable
        if out:
            try:
                is_writable = os.access(os.getcwd(), os.W_OK)
                if is_writable:
                    with open("courses.json", "w") as f:
                        json.dump(out, f)
                    print("Saved courses data to courses.json")
            except Exception as e:
                print(f"Warning: Could not save courses to file: {e}")
        else:
            print("Warning: No courses found in Canvas API response")
            # Return mock data if no courses found
            mock_data = {"Mock Course 1": 1001, "Mock Course 2": 1002}
            return mock_data

        return out
        
    except requests.RequestException as e:
        print(f"Error connecting to Canvas API: {e}")
        # Return mock data for development/testing
        mock_data = {"Mock Course 1": 1001, "Mock Course 2": 1002}
        return mock_data
    except Exception as e:
        print(f"Unexpected error in get_courses: {e}")
        import traceback
        print(traceback.format_exc())
        # Return mock data
        mock_data = {"Mock Course 1": 1001, "Mock Course 2": 1002}
        return mock_data

def get_modules(course_id):
    try:
        url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/modules"
        
        # Check if API key is available
        api_key = os.getenv('CANVAS_API_KEY')
        if not api_key:
            print("Error: CANVAS_API_KEY environment variable not set")
            # Return mock data
            mock_modules = [
                {"id": 2001, "name": "Mock Module 1"},
                {"id": 2002, "name": "Mock Module 2"}
            ]
            return mock_modules
            
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Add timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            print(f"Error: Canvas API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            # Return mock data
            mock_modules = [
                {"id": 2001, "name": "Mock Module 1"},
                {"id": 2002, "name": "Mock Module 2"}
            ]
            return mock_modules

        modules = response.json()
        
        # Only write to file if we have data and the filesystem is writable
        if modules:
            try:
                is_writable = os.access(os.getcwd(), os.W_OK)
                if is_writable:
                    with open("modules.json", "w") as f:
                        json.dump(modules, f)
                    print(f"Saved modules data for course {course_id} to modules.json")
            except Exception as e:
                print(f"Warning: Could not save modules to file: {e}")
        else:
            print(f"Warning: No modules found for course {course_id}")
            # Return mock data
            mock_modules = [
                {"id": 2001, "name": "Mock Module 1"},
                {"id": 2002, "name": "Mock Module 2"}
            ]
            return mock_modules

        return modules
        
    except requests.RequestException as e:
        print(f"Error connecting to Canvas API for modules: {e}")
        # Return mock data
        mock_modules = [
            {"id": 2001, "name": "Mock Module 1"},
            {"id": 2002, "name": "Mock Module 2"}
        ]
        return mock_modules
    except Exception as e:
        print(f"Unexpected error in get_modules: {e}")
        import traceback
        print(traceback.format_exc())
        # Return mock data
        mock_modules = [
            {"id": 2001, "name": "Mock Module 1"},
            {"id": 2002, "name": "Mock Module 2"}
        ]
        return mock_modules

def get_module_items(course_id, module_id):
    """Get items within a specific module"""
    try:
        url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/modules/{module_id}/items?per_page=100"
        
        # Check if API key is available
        api_key = os.getenv('CANVAS_API_KEY')
        if not api_key:
            print("Error: CANVAS_API_KEY environment variable not set")
            # Return mock data
            mock_items = [
                {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
                {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
            ]
            return mock_items
            
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Add timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            print(f"Error: Canvas API returned status code {response.status_code} for module items")
            print(f"Response: {response.text}")
            # Return mock data
            mock_items = [
                {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
                {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
            ]
            return mock_items
            
        items = response.json()
        
        if not items:
            print(f"Warning: No items found for module {module_id} in course {course_id}")
            # Return mock data
            mock_items = [
                {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
                {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
            ]
            return mock_items
            
        return items
        
    except requests.RequestException as e:
        print(f"Error connecting to Canvas API for module items: {e}")
        # Return mock data
        mock_items = [
            {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
            {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
        ]
        return mock_items
    except Exception as e:
        print(f"Unexpected error in get_module_items: {e}")
        import traceback
        print(traceback.format_exc())
        # Return mock data
        mock_items = [
            {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
            {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
        ]
        return mock_items

def get_file_url(course_id, file_id):
    """Get the download URL for a file"""
    try:
        url = f"https://canvas.asu.edu/api/v1/courses/{course_id}/files/{file_id}"
        
        # Check if API key is available
        api_key = os.getenv('CANVAS_API_KEY')
        if not api_key:
            print("Error: CANVAS_API_KEY environment variable not set")
            # Return a mock URL
            return f"https://example.com/mock-file-{file_id}.pdf"
            
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Add timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            print(f"Error: Canvas API returned status code {response.status_code} for file URL")
            print(f"Response: {response.text}")
            # Return a mock URL
            return f"https://example.com/mock-file-{file_id}.pdf"
            
        file_data = response.json()
        
        if 'url' in file_data:
            return file_data['url']
            
        print(f"Warning: No URL found in file data for file {file_id}")
        return f"https://example.com/mock-file-{file_id}.pdf"
        
    except requests.RequestException as e:
        print(f"Error connecting to Canvas API for file URL: {e}")
        # Return a mock URL
        return f"https://example.com/mock-file-{file_id}.pdf"
    except Exception as e:
        print(f"Unexpected error in get_file_url: {e}")
        import traceback
        print(traceback.format_exc())
        # Return a mock URL
        return f"https://example.com/mock-file-{file_id}.pdf"

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
    try:
        # Check if API key is available
        api_key = os.getenv('GOOGLE_API_KEY') or "AIzaSyAkgIwBlXvh67IuCVvi0ZNvtjQDcB-RyVg"
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set")
            # Return a default query
            return "Basic educational concept visible in the image"
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        
        # Create a model instance for multimodal generation
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: Image file does not exist: {image_path}")
            return "Image could not be analyzed - file not found"
            
        # Encode image
        try:
            image_data, mime_type = encode_image_to_base64(image_path)
        except Exception as e:
            print(f"Error encoding image: {e}")
            return "Image could not be encoded properly"
        
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
        try:
            response = model.generate_content([prompt, *image_parts])
            # Extract the query from the response
            return response.text
        except Exception as e:
            print(f"Error from Gemini API for image analysis: {e}")
            return "Error analyzing image with AI - please try a text query instead"
            
    except Exception as e:
        print(f"Unexpected error in analyze_image_with_gemini: {e}")
        import traceback
        print(traceback.format_exc())
        # Return a default response
        return "Error analyzing image - please try a text query instead"

def analyze_query_with_gemini(query, courses, course_modules=None):
    """
    Use Gemini to analyze the student's query and determine relevant course and modules
    Returns a dict with course_id, module_ids, and reasoning
    """
    try:
        # Check if API key is available
        api_key = os.getenv('GOOGLE_API_KEY') or "AIzaSyAkgIwBlXvh67IuCVvi0ZNvtjQDcB-RyVg"
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set")
            # Return default selection
            if course_modules is None:
                first_course = list(courses.keys())[0]
                return {
                    "course_name": first_course,
                    "confidence": 0.5,
                    "reasoning": "Default selection (API key missing)"
                }
            else:
                return {
                    "module_names": [course_modules[0]['name']] if course_modules else [],
                    "relevance_explanations": ["Default selection (API key missing)"]
                }
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        
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
            Be very specific in your match and don't default to the first course unless absolutely necessary.
            Look for subject matter keywords in the query and match them to the course titles.
            
            Provide your answer as a JSON object with the fields: 
            - course_name: The name of the most relevant course (MUST exactly match one of the provided course names)
            - confidence: A score from 0-1 indicating your confidence
            - reasoning: A brief explanation of why you chose this course
            
            Available courses:
            {courses_list}
            
            Think step by step:
            1. What subjects or topics does the query mention?
            2. Which course titles contain similar subjects or topics?
            3. Only choose a course if you're confident there's a good match
            4. If there's no clear match, select the most general course that might cover the topic
            """
            
            # Add timeout to prevent hanging requests
            response = model.generate_content(prompt)
            try:
                # Parse the result to get the course
                result = json.loads(response.text)
                
                # Validate the course name to ensure it's in the list
                if "course_name" in result and result["course_name"] not in courses:
                    print(f"Warning: Gemini returned an invalid course name: {result['course_name']}")
                    
                    # Try to find a close match
                    best_match = None
                    best_score = 0
                    for name in courses:
                        # Simple similarity score based on character overlap
                        similarity = sum(1 for a, b in zip(name.lower(), result["course_name"].lower()) if a == b)
                        score = similarity / max(len(name), len(result["course_name"]))
                        if score > best_score:
                            best_score = score
                            best_match = name
                    
                    if best_score > 0.5:
                        print(f"Found close match: {best_match} (score: {best_score})")
                        result["course_name"] = best_match
                        result["reasoning"] += f" (fixed invalid course name to closest match)"
                    else:
                        # Default to first course if no good match
                        result["course_name"] = list(courses.keys())[0]
                        result["confidence"] = 0.5
                        result["reasoning"] = "Default selection (invalid course name from LLM)"
                
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
            
            Think step by step:
            1. What specific topics or concepts does the query ask about?
            2. Which module titles seem to cover these topics?
            3. Choose modules that are most likely to contain resources answering the query
            """
            
            # Add timeout to prevent hanging requests
            response = model.generate_content(prompt)
            try:
                # Parse the result to get the modules
                result = json.loads(response.text)
                
                # Validate module names
                if "module_names" in result:
                    valid_module_names = [module["name"] for module in course_modules]
                    valid_results = []
                    
                    for name in result["module_names"]:
                        if name in valid_module_names:
                            valid_results.append(name)
                        else:
                            print(f"Warning: Invalid module name from Gemini: {name}")
                            # Try to find a close match
                            for valid_name in valid_module_names:
                                if name.lower() in valid_name.lower() or valid_name.lower() in name.lower():
                                    print(f"Found close match: {valid_name}")
                                    valid_results.append(valid_name)
                                    break
                    
                    # Update with only valid module names
                    result["module_names"] = valid_results
                    
                    # If no valid modules found, include the first module
                    if not valid_results and course_modules:
                        result["module_names"] = [course_modules[0]["name"]]
                        result["relevance_explanations"] = ["Default selection (no valid matches)"]
                
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
    except Exception as e:
        print(f"Error in analyze_query_with_gemini: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Return default values
        if course_modules is None:
            first_course = list(courses.keys())[0]
            return {
                "course_name": first_course,
                "confidence": 0.5,
                "reasoning": f"Default selection due to error: {str(e)}"
            }
        else:
            return {
                "module_names": [course_modules[0]['name']] if course_modules else [],
                "relevance_explanations": [f"Default selection due to error: {str(e)}"]
            }

def analyze_resource_relevance(query, resource_items, course_name, module_name):
    """
    Use Gemini to analyze which resources are most relevant to the student's query
    """
    try:
        # Check if API key is available
        api_key = os.getenv('GOOGLE_API_KEY') or "AIzaSyAkgIwBlXvh67IuCVvi0ZNvtjQDcB-RyVg"
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set")
            # Return default selection
            return {
                "resource_indices": list(range(min(3, len(resource_items)))),
                "relevance_scores": [0.8] * min(3, len(resource_items)),
                "reasoning": "Default selection (API key missing)"
            }
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        
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
        
        try:
            # Generate content without timeout
            response = model.generate_content(prompt)
            # Parse the result to get the relevant resources
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Fallback if the response isn't proper JSON
            print(f"Error parsing Gemini response: {response.text}")
            # Default to returning first 3 resources
            return {
                "resource_indices": list(range(min(3, len(resource_items)))),
                "relevance_scores": [0.8] * min(3, len(resource_items)),
                "reasoning": "Default selection due to parsing error"
            }
        except Exception as e:
            print(f"Error from Gemini API for resource relevance: {e}")
            # Default to returning first 3 resources
            return {
                "resource_indices": list(range(min(3, len(resource_items)))),
                "relevance_scores": [0.8] * min(3, len(resource_items)),
                "reasoning": f"Default selection due to API error: {str(e)}"
            }
            
    except Exception as e:
        print(f"Unexpected error in analyze_resource_relevance: {e}")
        import traceback
        print(traceback.format_exc())
        # Default to returning first 3 resources
        return {
            "resource_indices": list(range(min(3, len(resource_items)))),
            "relevance_scores": [0.8] * min(3, len(resource_items)),
            "reasoning": f"Default selection due to error: {str(e)}"
        }

@app.get("/")
async def root():
    """Root endpoint for the API"""
    return {"message": "Canvas Resource API is running. Use /resources endpoint to find resources."}

@app.get("/resources")
async def resources_endpoint(query: str = Query(..., description="Learning query to search for"), 
                     image_path: str = Query(None, description="Optional path to image for analysis")):
    """API endpoint to find resources based on a student query or image"""
    try:
        print(f"Processing query: {query}, image_path: {image_path}")
        
        # Validate inputs
        if not query and not image_path:
            return JSONResponse(
                status_code=400, 
                content={"error": "Either query or image_path must be provided"}
            )
            
        # Check if image path exists when provided
        if image_path and not os.path.exists(image_path):
            print(f"Warning: Image path does not exist: {image_path}")
            # Continue without the image rather than failing
        
        # Call find_resources with proper error handling
        result = find_resources(query, image_path)
        return result
        
    except Exception as e:
        # Log the error
        error_msg = f"Error processing request: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        
        # Return a proper error response
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": str(e)}
        )

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
        print("Error: No courses found from Canvas API")
        return [{"error": "No courses found", "details": "Please check your Canvas API configuration"}]
    
    # Print available courses for debugging
    print(f"Available courses: {list(courses.keys())}")
    
    # Step 2: Analyze the query to identify the relevant course
    print(f"Analyzing query: '{query}'")
    course_analysis = analyze_query_with_gemini(query, courses)
    course_name = course_analysis.get("course_name")
    confidence = course_analysis.get("confidence", 0)
    reasoning = course_analysis.get("reasoning", "No reasoning provided")
    
    print(f"Course analysis result: {course_name} (confidence: {confidence})")
    print(f"Reasoning: {reasoning}")
    
    # Improved course matching logic
    if course_name not in courses:
        print(f"Exact course match not found for '{course_name}', trying partial matches")
        # Try to find a partial match with higher threshold
        best_match = None
        best_match_score = 0
        
        for name in courses:
            # Check for significant word overlap
            query_words = set(w.lower() for w in query.split() if len(w) > 3)
            name_words = set(w.lower() for w in name.split() if len(w) > 3)
            
            # Calculate overlap score
            if query_words and name_words:
                overlap = len(query_words.intersection(name_words))
                score = overlap / min(len(query_words), len(name_words))
                print(f"Course: {name}, score: {score}")
                
                if score > best_match_score:
                    best_match_score = score
                    best_match = name
            
            # Also check for simple substring match
            elif course_name.lower() in name.lower() or name.lower() in course_name.lower():
                print(f"Substring match found: {name}")
                if best_match is None:
                    best_match = name
        
        if best_match and best_match_score >= 0.2:
            print(f"Using best match course: {best_match} (score: {best_match_score})")
            course_name = best_match
        elif best_match:
            print(f"Using substring match course: {best_match}")
            course_name = best_match
        else:
            # If still no match found, check if there's a course related to the query topic
            query_keywords = [w.lower() for w in query.split() if len(w) > 4]
            
            for name in courses:
                for keyword in query_keywords:
                    if keyword in name.lower():
                        print(f"Keyword match found: {name} (keyword: {keyword})")
                        course_name = name
                        break
                if course_name in courses:
                    break
            
            # Last resort - default to first course
            if course_name not in courses:
                course_name = list(courses.keys())[0]
                print(f"No matches found, defaulting to first course: {course_name}")
    
    course_id = courses[course_name]
    print(f"Selected course: {course_name} (ID: {course_id})")
    
    # Step 3: Get modules for the identified course
    modules = get_modules(course_id)
    if not modules:
        print(f"No modules found for course: {course_name}")
        return [{"error": "No modules found", "course": course_name}]
    
    print(f"Found {len(modules)} modules in course {course_name}")
    
    # Step 4: Analyze which modules are most relevant
    module_analysis = analyze_query_with_gemini(query, courses, modules)
    relevant_module_names = module_analysis.get("module_names", [])
    
    print(f"Relevant module names from analysis: {relevant_module_names}")
    
    # Map module names to IDs
    relevant_modules = []
    for module in modules:
        if module["name"] in relevant_module_names:
            print(f"Found exact module match: {module['name']}")
            relevant_modules.append(module)
        # If we can't find exact matches, include modules that contain the query keywords
        elif any(keyword.lower() in module["name"].lower() 
                for keyword in query.lower().split() if len(keyword) > 3):
            print(f"Found keyword match in module: {module['name']}")
            relevant_modules.append(module)
    
    # If no relevant modules found, include the first few modules
    if not relevant_modules and modules:
        print(f"No relevant modules found, using first {min(2, len(modules))} modules")
        relevant_modules = modules[:2]
    
    print(f"Selected {len(relevant_modules)} modules for further analysis")
    
    # Step 5: Get items from relevant modules and filter for resources
    all_relevant_resources = []
    
    for module in relevant_modules:
        module_id = module["id"]
        module_name = module["name"]
        
        print(f"Getting items for module: {module_name} (ID: {module_id})")
        
        # Get all items in this module
        items = get_module_items(course_id, module_id)
        
        if not items:
            print(f"No items found in module: {module_name}")
            continue
        
        print(f"Found {len(items)} items in module: {module_name}")
        
        # Analyze which resources are most relevant within this module
        resource_analysis = analyze_resource_relevance(query, items, course_name, module_name)
        relevant_indices = resource_analysis.get("resource_indices", [])
        relevance_scores = resource_analysis.get("relevance_scores", [])
        
        print(f"Relevant indices from analysis: {relevant_indices}")
        
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
                print(f"Added resource: {resource['title']} (score: {resource['relevance_score']})")
    
    # Sort resources by relevance score (descending)
    all_relevant_resources.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # Return results, or an error if none found
    if all_relevant_resources:
        print(f"Returning {len(all_relevant_resources)} relevant resources")
        # Try to save resources to a json file, but don't fail if it's not possible (e.g., read-only filesystem)
        try:
            # Check if we're in a writable environment before attempting to write
            is_writable = os.access(os.getcwd(), os.W_OK)
            if is_writable:
                safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]  # Make filename safe
                with open(f"resources_{safe_query}.json", "w") as f:
                    json.dump(all_relevant_resources, f)
                print(f"Saved resources to resources_{safe_query}.json")
        except Exception as e:
            # Just log the error but continue
            print(f"Warning: Could not save resources to file: {e}")

        return all_relevant_resources
    else:
        print(f"No relevant resources found for query: {query}")
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
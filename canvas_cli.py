#!/usr/bin/env python
import argparse
from canvas import find_resources, test_agent
import os

def main():
    """Command-line interface for the Canvas AI Learning Resource Agent"""
    parser = argparse.ArgumentParser(
        description="Find relevant Canvas resources based on your question or image"
    )
    parser.add_argument(
        "--query", "-q", 
        type=str,
        help="Your learning question (e.g., 'I don't understand orthogonalization of matrices')"
    )
    parser.add_argument(
        "--image", "-i", 
        type=str,
        help="Path to an image file containing educational content to analyze"
    )
    parser.add_argument(
        "--test", "-t", 
        action="store_true",
        help="Run test cases with predefined prompts and images"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Print detailed information about each resource"
    )
    
    args = parser.parse_args()
    
    if args.test:
        print("Running test cases...")
        test_agent()
        return
    
    if not args.query and not args.image:
        parser.print_help()
        return
    
    query = args.query or ""
    
    if args.image:
        if not os.path.exists(args.image):
            print(f"Error: Image file not found at path '{args.image}'")
            return
        
        print(f"Analyzing image: {args.image}")
        print(f"Query context: {query}")
        print("Please wait, this may take a few moments...\n")
    else:
        print(f"Searching for resources related to: {query}")
        print("Please wait, this may take a few moments...\n")
    
    # Get resources for the query
    resources = find_resources(query, image_path=args.image)
    
    if resources and "error" in resources[0]:
        print(f"Error: {resources[0].get('error')}")
        if 'details' in resources[0]:
            print(f"Details: {resources[0].get('details')}")
        return
    
    print(f"Found {len(resources)} relevant resources:\n")
    
    for i, resource in enumerate(resources):
        print(f"{i+1}. {resource.get('title', 'Untitled')}")
        print(f"   URL: {resource.get('url', 'No URL')}")
        
        if args.verbose:
            print(f"   Type: {resource.get('type', 'Unknown')}")
            print(f"   Course: {resource.get('course', 'Unknown')}")
            print(f"   Module: {resource.get('module', 'Unknown')}")
            print(f"   Relevance Score: {resource.get('relevance_score', 0):.2f}")
        
        print()
    
    print("\nTo get more details, run with the --verbose flag.")

if __name__ == "__main__":
    main() 
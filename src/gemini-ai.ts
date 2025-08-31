// Google Gemini AI functions
import { GoogleGenerativeAI } from '@google/generative-ai';
import { Course, Module, ModuleItem, CourseAnalysis, ModuleAnalysis, ResourceAnalysis, Env } from './types';

export async function analyzeImageWithGemini(imageData: string, mimeType: string, env: Env): Promise<string> {
  try {
    // Check if API key is available
    const apiKey = env.GOOGLE_API_KEY;
    if (!apiKey) {
      console.log("Error: GOOGLE_API_KEY environment variable not set");
      // Return a default query
      return "Basic educational concept visible in the image";
    }
    
    // Initialize Gemini
    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Create a model instance for multimodal generation
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
    
    // Create the prompt for image analysis
    const prompt = `
    This is an educational image. Please analyze it and extract the main learning concept 
    or topic being illustrated. Describe what subject area this relates to and any key 
    terminology visible in the image. Give your response as a detailed query that I could
    use to find learning resources about this topic.
    `;
    
    // Prepare the image for the API
    const imagePart = {
      inlineData: {
        data: imageData,
        mimeType: mimeType,
      },
    };
    
    // Generate content with the image
    try {
      const result = await model.generateContent([prompt, imagePart]);
      const response = await result.response;
      return response.text();
    } catch (error: any) {
      console.log(`Error from Gemini API for image analysis: ${error.message}`);
      return "Error analyzing image with AI - please try a text query instead";
    }
    
  } catch (error: any) {
    console.log(`Unexpected error in analyzeImageWithGemini: ${error.message}`);
    // Return a default response
    return "Error analyzing image - please try a text query instead";
  }
}

export async function analyzeQueryWithGemini(
  query: string, 
  courses: Course, 
  env: Env, 
  courseModules?: Module[]
): Promise<CourseAnalysis | ModuleAnalysis> {
  try {
    // Check if API key is available
    const apiKey = env.GOOGLE_API_KEY;
    if (!apiKey) {
      console.log("Error: GOOGLE_API_KEY environment variable not set");
      // Return default selection
      if (courseModules === undefined) {
        const firstCourse = Object.keys(courses)[0];
        return {
          course_name: firstCourse,
          confidence: 0.5,
          reasoning: "Default selection (API key missing)"
        };
      } else {
        return {
          module_names: courseModules.length > 0 ? [courseModules[0].name] : [],
          relevance_explanations: ["Default selection (API key missing)"]
        };
      }
    }
    
    // Initialize Gemini
    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Create a model instance
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
    
    if (courseModules === undefined) {
      // First stage: identify the correct course
      const coursesList = Object.keys(courses).map(name => `- ${name}`).join('\n');
      
      const prompt = `
      You are an AI assistant for educational content. A student has the following question:
      
      "${query}"
      
      Based on this question, which of the following courses is the student most likely referring to? 
      Be very specific in your match and don't default to the first course unless absolutely necessary.
      Look for subject matter keywords in the query and match them to the course titles.
      
      Provide your answer as a JSON object with the fields: 
      - course_name: The name of the most relevant course (MUST exactly match one of the provided course names)
      - confidence: A score from 0-1 indicating your confidence
      - reasoning: A brief explanation of why you chose this course
      
      Available courses:
      ${coursesList}
      
      Think step by step:
      1. What subjects or topics does the query mention?
      2. Which course titles contain similar subjects or topics?
      3. Only choose a course if you're confident there's a good match
      4. If there's no clear match, select the most general course that might cover the topic
      `;
      
      try {
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const responseText = response.text();
        
        try {
          // Parse the result to get the course
          const result = JSON.parse(responseText);
          
          // Validate the course name to ensure it's in the list
          if ("course_name" in result && !(result.course_name in courses)) {
            console.log(`Warning: Gemini returned an invalid course name: ${result.course_name}`);
            
            // Try to find a close match
            let bestMatch = null;
            let bestScore = 0;
            for (const name of Object.keys(courses)) {
              // Simple similarity score based on character overlap
              const similarity = [...name.toLowerCase()].filter((char, i) => 
                char === result.course_name.toLowerCase()[i]
              ).length;
              const score = similarity / Math.max(name.length, result.course_name.length);
              if (score > bestScore) {
                bestScore = score;
                bestMatch = name;
              }
            }
            
            if (bestScore > 0.5) {
              console.log(`Found close match: ${bestMatch} (score: ${bestScore})`);
              result.course_name = bestMatch;
              result.reasoning += ` (fixed invalid course name to closest match)`;
            } else {
              // Default to first course if no good match
              result.course_name = Object.keys(courses)[0];
              result.confidence = 0.5;
              result.reasoning = "Default selection (invalid course name from LLM)";
            }
          }
          
          return result as CourseAnalysis;
        } catch (parseError) {
          // Fallback if the response isn't proper JSON
          console.log(`Error parsing Gemini response: ${responseText}`);
          // Make a best guess based on the response text
          for (const courseName of Object.keys(courses)) {
            if (responseText.toLowerCase().includes(courseName.toLowerCase())) {
              return {
                course_name: courseName,
                confidence: 0.7,
                reasoning: "Extracted from response"
              };
            }
          }
          // Default to first course if no match
          const firstCourse = Object.keys(courses)[0];
          return {
            course_name: firstCourse,
            confidence: 0.5,
            reasoning: "Default selection"
          };
        }
      } catch (error: any) {
        console.log(`Error from Gemini API: ${error.message}`);
        const firstCourse = Object.keys(courses)[0];
        return {
          course_name: firstCourse,
          confidence: 0.5,
          reasoning: `Default selection due to API error: ${error.message}`
        };
      }
    } else {
      // Second stage: identify relevant modules in the course
      const modulesList = courseModules.map(module => `- ${module.name}`).join('\n');
      
      const prompt = `
      You are an AI assistant for educational content. A student has the following question:
      
      "${query}"
      
      Based on this question, which of the following modules in the course are most relevant?
      Return a JSON object with:
      - module_names: An array of names of the most relevant modules (maximum 3)
      - relevance_explanations: Brief explanation for each module's relevance
      
      Available modules:
      ${modulesList}
      
      Think step by step:
      1. What specific topics or concepts does the query ask about?
      2. Which module titles seem to cover these topics?
      3. Choose modules that are most likely to contain resources answering the query
      `;
      
      try {
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const responseText = response.text();
        
        try {
          // Parse the result to get the modules
          const result = JSON.parse(responseText);
          
          // Validate module names
          if ("module_names" in result) {
            const validModuleNames = courseModules.map(module => module.name);
            const validResults: string[] = [];
            
            for (const name of result.module_names) {
              if (validModuleNames.includes(name)) {
                validResults.push(name);
              } else {
                console.log(`Warning: Invalid module name from Gemini: ${name}`);
                // Try to find a close match
                for (const validName of validModuleNames) {
                  if (name.toLowerCase().includes(validName.toLowerCase()) || 
                      validName.toLowerCase().includes(name.toLowerCase())) {
                    console.log(`Found close match: ${validName}`);
                    validResults.push(validName);
                    break;
                  }
                }
              }
            }
            
            // Update with only valid module names
            result.module_names = validResults;
            
            // If no valid modules found, include the first module
            if (validResults.length === 0 && courseModules.length > 0) {
              result.module_names = [courseModules[0].name];
              result.relevance_explanations = ["Default selection (no valid matches)"];
            }
          }
          
          return result as ModuleAnalysis;
        } catch (parseError) {
          // Fallback if the response isn't proper JSON
          console.log(`Error parsing Gemini response: ${responseText}`);
          // Make a best guess based on the response text
          const relevantModules: string[] = [];
          for (const module of courseModules) {
            if (responseText.toLowerCase().includes(module.name.toLowerCase())) {
              relevantModules.push(module.name);
            }
          }
          
          if (relevantModules.length === 0 && courseModules.length > 0) {
            // Default to first module if no match
            relevantModules.push(courseModules[0].name);
          }
          
          return {
            module_names: relevantModules.slice(0, 3),
            relevance_explanations: Array(relevantModules.slice(0, 3).length).fill("Extracted from response")
          };
        }
      } catch (error: any) {
        console.log(`Error from Gemini API: ${error.message}`);
        return {
          module_names: courseModules.length > 0 ? [courseModules[0].name] : [],
          relevance_explanations: [`Default selection due to API error: ${error.message}`]
        };
      }
    }
  } catch (error: any) {
    console.log(`Error in analyzeQueryWithGemini: ${error.message}`);
    
    // Return default values
    if (courseModules === undefined) {
      const firstCourse = Object.keys(courses)[0];
      return {
        course_name: firstCourse,
        confidence: 0.5,
        reasoning: `Default selection due to error: ${error.message}`
      };
    } else {
      return {
        module_names: courseModules.length > 0 ? [courseModules[0].name] : [],
        relevance_explanations: [`Default selection due to error: ${error.message}`]
      };
    }
  }
}

export async function analyzeResourceRelevance(
  query: string, 
  resourceItems: ModuleItem[], 
  courseName: string, 
  moduleName: string, 
  env: Env
): Promise<ResourceAnalysis> {
  try {
    // Check if API key is available
    const apiKey = env.GOOGLE_API_KEY;
    if (!apiKey) {
      console.log("Error: GOOGLE_API_KEY environment variable not set");
      // Return default selection
      return {
        resource_indices: Array.from({length: Math.min(3, resourceItems.length)}, (_, i) => i),
        relevance_scores: Array(Math.min(3, resourceItems.length)).fill(0.8),
        reasoning: "Default selection (API key missing)"
      };
    }
    
    // Initialize Gemini
    const genAI = new GoogleGenerativeAI(apiKey);
    
    // Create a model instance
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
    
    // Format the resources as a list for the prompt
    const resourcesList = resourceItems.map(item => 
      `- ${item.title || 'Untitled'} (Type: ${item.type || 'Unknown'})`
    ).join('\n');
    
    const prompt = `
    You are an AI assistant for educational content. A student has the following question:
    
    "${query}"
    
    This question relates to the course "${courseName}" in the module "${moduleName}".
    
    Based on this question, which of the following resources would be most helpful to the student?
    Return a JSON object with:
    - resource_indices: An array of indices (0-based) of the most relevant resources (maximum 5)
    - relevance_scores: An array of relevance scores (0-1) corresponding to each resource
    - reasoning: Brief explanation of why these resources are relevant
    
    Available resources:
    ${resourcesList}
    `;
    
    try {
      // Generate content
      const result = await model.generateContent(prompt);
      const response = await result.response;
      const responseText = response.text();
      
      // Parse the result to get the relevant resources
      const parsedResult = JSON.parse(responseText);
      return parsedResult as ResourceAnalysis;
    } catch (parseError: any) {
      // Fallback if the response isn't proper JSON
      console.log(`Error parsing Gemini response: ${parseError.message}`);
      // Default to returning first 3 resources
      return {
        resource_indices: Array.from({length: Math.min(3, resourceItems.length)}, (_, i) => i),
        relevance_scores: Array(Math.min(3, resourceItems.length)).fill(0.8),
        reasoning: "Default selection due to parsing error"
      };
    }
  } catch (error: any) {
    console.log(`Error from Gemini API for resource relevance: ${error.message}`);
    // Default to returning first 3 resources
    return {
      resource_indices: Array.from({length: Math.min(3, resourceItems.length)}, (_, i) => i),
      relevance_scores: Array(Math.min(3, resourceItems.length)).fill(0.8),
      reasoning: `Default selection due to API error: ${error.message}`
    };
  }
}

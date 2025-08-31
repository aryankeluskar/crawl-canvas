// Main resource finding logic
import { Resource, Course, Module, CourseAnalysis, ModuleAnalysis, Env } from './types';
import { getCourses, getModules, getModuleItems, getFileUrl } from './canvas-api';
import { analyzeImageWithGemini, analyzeQueryWithGemini, analyzeResourceRelevance } from './gemini-ai';

export async function findResources(
  query: string, 
  env: Env, 
  imageData?: string, 
  mimeType?: string,
  requestHeaders?: Headers
): Promise<Resource[] | {error: string; details?: string; query?: string; course?: string}[]> {
  // If an image is provided, analyze it to get a query
  if (imageData && mimeType) {
    console.log("Analyzing image...");
    const imageQuery = await analyzeImageWithGemini(imageData, mimeType, env);
    // Combine the original query with the image analysis
    if (query) {
      query = `${query} - ${imageQuery}`;
    } else {
      query = imageQuery;
    }
    console.log(`Image analysis result: ${query}`);
  }
  
  // Step 1: Get all courses
  const courses = await getCourses(env, requestHeaders);
  if (!courses || Object.keys(courses).length === 0) {
    console.log("Error: No courses found from Canvas API");
    return [{"error": "No courses found", "details": "Please check your Canvas API configuration"}];
  }
  
  // Print available courses for debugging
  console.log(`Available courses: ${Object.keys(courses).join(', ')}`);
  
  // Step 2: Analyze the query to identify the relevant course
  console.log(`Analyzing query: '${query}'`);
  const courseAnalysis = await analyzeQueryWithGemini(query, courses, env) as CourseAnalysis;
  let courseName = courseAnalysis.course_name;
  const confidence = courseAnalysis.confidence || 0;
  const reasoning = courseAnalysis.reasoning || "No reasoning provided";
  
  console.log(`Course analysis result: ${courseName} (confidence: ${confidence})`);
  console.log(`Reasoning: ${reasoning}`);
  
  // Improved course matching logic
  if (!(courseName in courses)) {
    console.log(`Exact course match not found for '${courseName}', trying partial matches`);
    // Try to find a partial match with higher threshold
    let bestMatch = null;
    let bestMatchScore = 0;
    
    for (const name of Object.keys(courses)) {
      // Check for significant word overlap
      const queryWords = new Set(query.split(' ').filter(w => w.length > 3).map(w => w.toLowerCase()));
      const nameWords = new Set(name.split(' ').filter(w => w.length > 3).map(w => w.toLowerCase()));
      
      // Calculate overlap score
      if (queryWords.size > 0 && nameWords.size > 0) {
        const intersection = new Set([...queryWords].filter(x => nameWords.has(x)));
        const score = intersection.size / Math.min(queryWords.size, nameWords.size);
        console.log(`Course: ${name}, score: ${score}`);
        
        if (score > bestMatchScore) {
          bestMatchScore = score;
          bestMatch = name;
        }
      }
      
      // Also check for simple substring match
      if (courseName.toLowerCase().includes(name.toLowerCase()) || name.toLowerCase().includes(courseName.toLowerCase())) {
        console.log(`Substring match found: ${name}`);
        if (bestMatch === null) {
          bestMatch = name;
        }
      }
    }
    
    if (bestMatch && bestMatchScore >= 0.2) {
      console.log(`Using best match course: ${bestMatch} (score: ${bestMatchScore})`);
      courseName = bestMatch;
    } else if (bestMatch) {
      console.log(`Using substring match course: ${bestMatch}`);
      courseName = bestMatch;
    } else {
      // If still no match found, check if there's a course related to the query topic
      const queryKeywords = query.split(' ').filter(w => w.length > 4).map(w => w.toLowerCase());
      
      for (const name of Object.keys(courses)) {
        for (const keyword of queryKeywords) {
          if (name.toLowerCase().includes(keyword)) {
            console.log(`Keyword match found: ${name} (keyword: ${keyword})`);
            courseName = name;
            break;
          }
        }
        if (courseName in courses) {
          break;
        }
      }
      
      // Last resort - default to first course
      if (!(courseName in courses)) {
        courseName = Object.keys(courses)[0];
        console.log(`No matches found, defaulting to first course: ${courseName}`);
      }
    }
  }
  
  const courseId = courses[courseName];
  console.log(`Selected course: ${courseName} (ID: ${courseId})`);
  
  // Step 3: Get modules for the identified course
  const modules = await getModules(courseId, env, requestHeaders);
  if (!modules || modules.length === 0) {
    console.log(`No modules found for course: ${courseName}`);
    return [{"error": "No modules found", "course": courseName}];
  }
  
  console.log(`Found ${modules.length} modules in course ${courseName}`);
  
  // Step 4: Analyze which modules are most relevant
  const moduleAnalysis = await analyzeQueryWithGemini(query, courses, env, modules) as ModuleAnalysis;
  const relevantModuleNames = moduleAnalysis.module_names || [];
  
  console.log(`Relevant module names from analysis: ${relevantModuleNames.join(', ')}`);
  
  // Map module names to IDs
  const relevantModules: Module[] = [];
  for (const module of modules) {
    if (relevantModuleNames.includes(module.name)) {
      console.log(`Found exact module match: ${module.name}`);
      relevantModules.push(module);
    }
    // If we can't find exact matches, include modules that contain the query keywords
    else if (query.toLowerCase().split(' ').filter(keyword => keyword.length > 3).some(keyword => 
      module.name.toLowerCase().includes(keyword)
    )) {
      console.log(`Found keyword match in module: ${module.name}`);
      relevantModules.push(module);
    }
  }
  
  // If no relevant modules found, include the first few modules
  if (relevantModules.length === 0 && modules.length > 0) {
    console.log(`No relevant modules found, using first ${Math.min(2, modules.length)} modules`);
    relevantModules.push(...modules.slice(0, 2));
  }
  
  console.log(`Selected ${relevantModules.length} modules for further analysis`);
  
  // Step 5: Get items from relevant modules and filter for resources
  const allRelevantResources: Resource[] = [];
  
  for (const module of relevantModules) {
    const moduleId = module.id;
    const moduleName = module.name;
    
    console.log(`Getting items for module: ${moduleName} (ID: ${moduleId})`);
    
    // Get all items in this module
    const items = await getModuleItems(courseId, moduleId, env, requestHeaders);
    
    if (!items || items.length === 0) {
      console.log(`No items found in module: ${moduleName}`);
      continue;
    }
    
    console.log(`Found ${items.length} items in module: ${moduleName}`);
    
    // Analyze which resources are most relevant within this module
    const resourceAnalysis = await analyzeResourceRelevance(query, items, courseName, moduleName, env);
    const relevantIndices = resourceAnalysis.resource_indices || [];
    const relevanceScores = resourceAnalysis.relevance_scores || [];
    
    console.log(`Relevant indices from analysis: ${relevantIndices.join(', ')}`);
    
    // Add the relevant resources to our results
    for (let idxPos = 0; idxPos < relevantIndices.length; idxPos++) {
      const idx = relevantIndices[idxPos];
      if (idx < items.length) {
        const item = items[idx];
        // Format the resource for the response
        const resource: Resource = {
          title: item.title || "Untitled Resource",
          type: item.type || "Unknown",
          url: item.html_url || "",
          course: courseName,
          module: moduleName,
          relevance_score: idxPos < relevanceScores.length ? relevanceScores[idxPos] : 0.5
        };
        
        // For file resources, get the actual file URL
        if (item.type === "File" && item.content_id) {
          const fileUrl = await getFileUrl(courseId, item.content_id, env, requestHeaders);
          if (fileUrl) {
            resource.url = fileUrl;
          }
        }
        
        allRelevantResources.push(resource);
        console.log(`Added resource: ${resource.title} (score: ${resource.relevance_score})`);
      }
    }
  }
  
  // Sort resources by relevance score (descending)
  allRelevantResources.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
  
  // Return results, or an error if none found
  if (allRelevantResources.length > 0) {
    console.log(`Returning ${allRelevantResources.length} relevant resources`);
    return allRelevantResources;
  } else {
    console.log(`No relevant resources found for query: ${query}`);
    return [{"error": "No relevant resources found", "query": query, "course": courseName}];
  }
}

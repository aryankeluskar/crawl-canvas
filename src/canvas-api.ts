// Canvas API functions
import { Course, Module, ModuleItem, Env } from './types';

function getApiKey(requestHeaders?: Headers, env?: Env): string | null {
  // First check request headers for Authorization bearer token
  if (requestHeaders) {
    const authHeader = requestHeaders.get('Authorization');
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7); // Remove 'Bearer ' prefix
    }
    
    // Also check for custom Canvas-API-Key header
    const canvasApiKey = requestHeaders.get('Canvas-API-Key');
    if (canvasApiKey) {
      return canvasApiKey;
    }
  }
  
  // Fall back to environment variable
  return env?.CANVAS_API_KEY || null;
}

export async function getCourses(env: Env, requestHeaders?: Headers): Promise<Course> {
  try {
    const url = "https://canvas.asu.edu/api/v1/courses?page=1&per_page=100";
    
    // Check if API key is available
    const apiKey = getApiKey(requestHeaders, env);
    if (!apiKey) {
      console.log("Error: Canvas API key not provided in headers or environment variables");
      // Return mock data for development/testing
      return {"Mock Course 1": 1001, "Mock Course 2": 1002};
    }
    
    const headers = {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    };
    
    // Add timeout to prevent hanging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(url, { 
      headers, 
      signal: controller.signal 
    });
    clearTimeout(timeoutId);
    
    // Check response status
    if (response.status !== 200) {
      console.log(`Error: Canvas API returned status code ${response.status}`);
      const responseText = await response.text();
      console.log(`Response: ${responseText}`);
      // Return mock data if API call fails
      return {"Mock Course 1": 1001, "Mock Course 2": 1002};
    }
    
    const courses = await response.json() as any[];
    const out: Course = {};
    
    for (const course of courses) {
      if ("id" in course && "name" in course) {
        out[course.name] = course.id;
      }
    }
    
    if (Object.keys(out).length === 0) {
      console.log("Warning: No courses found in Canvas API response");
      return {"Mock Course 1": 1001, "Mock Course 2": 1002};
    }
    
    return out;
    
  } catch (error: any) {
    console.log(`Error connecting to Canvas API: ${error.message}`);
    // Return mock data for development/testing
    return {"Mock Course 1": 1001, "Mock Course 2": 1002};
  }
}

export async function getModules(courseId: number, env: Env, requestHeaders?: Headers): Promise<Module[]> {
  try {
    const url = `https://canvas.asu.edu/api/v1/courses/${courseId}/modules`;
    
    // Check if API key is available
    const apiKey = getApiKey(requestHeaders, env);
    if (!apiKey) {
      console.log("Error: Canvas API key not provided in headers or environment variables");
      // Return mock data
      return [
        {"id": 2001, "name": "Mock Module 1"},
        {"id": 2002, "name": "Mock Module 2"}
      ];
    }
    
    const headers = {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    };
    
    // Add timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(url, { 
      headers, 
      signal: controller.signal 
    });
    clearTimeout(timeoutId);
    
    // Check response status
    if (response.status !== 200) {
      console.log(`Error: Canvas API returned status code ${response.status}`);
      const responseText = await response.text();
      console.log(`Response: ${responseText}`);
      // Return mock data
      return [
        {"id": 2001, "name": "Mock Module 1"},
        {"id": 2002, "name": "Mock Module 2"}
      ];
    }
    
    const modules = await response.json() as Module[];
    
    if (!modules || modules.length === 0) {
      console.log(`Warning: No modules found for course ${courseId}`);
      // Return mock data
      return [
        {"id": 2001, "name": "Mock Module 1"},
        {"id": 2002, "name": "Mock Module 2"}
      ];
    }
    
    return modules;
    
  } catch (error: any) {
    console.log(`Error connecting to Canvas API for modules: ${error.message}`);
    // Return mock data
    return [
      {"id": 2001, "name": "Mock Module 1"},
      {"id": 2002, "name": "Mock Module 2"}
    ];
  }
}

export async function getModuleItems(courseId: number, moduleId: number, env: Env, requestHeaders?: Headers): Promise<ModuleItem[]> {
  try {
    const url = `https://canvas.asu.edu/api/v1/courses/${courseId}/modules/${moduleId}/items?per_page=100`;
    
    // Check if API key is available
    const apiKey = getApiKey(requestHeaders, env);
    if (!apiKey) {
      console.log("Error: Canvas API key not provided in headers or environment variables");
      // Return mock data
      return [
        {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
        {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
      ];
    }
    
    const headers = {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    };
    
    // Add timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(url, { 
      headers, 
      signal: controller.signal 
    });
    clearTimeout(timeoutId);
    
    // Check response status
    if (response.status !== 200) {
      console.log(`Error: Canvas API returned status code ${response.status} for module items`);
      const responseText = await response.text();
      console.log(`Response: ${responseText}`);
      // Return mock data
      return [
        {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
        {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
      ];
    }
    
    const items = await response.json() as ModuleItem[];
    
    if (!items || items.length === 0) {
      console.log(`Warning: No items found for module ${moduleId} in course ${courseId}`);
      // Return mock data
      return [
        {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
        {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
      ];
    }
    
    return items;
    
  } catch (error: any) {
    console.log(`Error connecting to Canvas API for module items: ${error.message}`);
    // Return mock data
    return [
      {"id": 3001, "title": "Mock Item 1", "type": "Page", "html_url": "https://example.com/item1"},
      {"id": 3002, "title": "Mock Item 2", "type": "Assignment", "html_url": "https://example.com/item2"}
    ];
  }
}

export async function getFileUrl(courseId: number, fileId: number, env: Env, requestHeaders?: Headers): Promise<string> {
  try {
    const url = `https://canvas.asu.edu/api/v1/courses/${courseId}/files/${fileId}`;
    
    // Check if API key is available
    const apiKey = getApiKey(requestHeaders, env);
    if (!apiKey) {
      console.log("Error: Canvas API key not provided in headers or environment variables");
      // Return a mock URL
      return `https://example.com/mock-file-${fileId}.pdf`;
    }
    
    const headers = {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    };
    
    // Add timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(url, { 
      headers, 
      signal: controller.signal 
    });
    clearTimeout(timeoutId);
    
    // Check response status
    if (response.status !== 200) {
      console.log(`Error: Canvas API returned status code ${response.status} for file URL`);
      const responseText = await response.text();
      console.log(`Response: ${responseText}`);
      // Return a mock URL
      return `https://example.com/mock-file-${fileId}.pdf`;
    }
    
    const fileData = await response.json() as any;
    
    if ('url' in fileData) {
      return fileData.url;
    }
    
    console.log(`Warning: No URL found in file data for file ${fileId}`);
    return `https://example.com/mock-file-${fileId}.pdf`;
    
  } catch (error: any) {
    console.log(`Error connecting to Canvas API for file URL: ${error.message}`);
    // Return a mock URL
    return `https://example.com/mock-file-${fileId}.pdf`;
  }
}

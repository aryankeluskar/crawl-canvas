import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { Env } from './types'
import { findResources } from './resource-finder'

const app = new Hono<{ Bindings: Env }>()

// Add CORS middleware
app.use('/*', cors({
  origin: ['*'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['*'],
  credentials: true,
}))

// API Routes
app.get('/', (c) => {
  return c.json({ message: "Canvas Resource API is running. Use /resources endpoint to find resources." });
});

// Minimal frontend UI
app.get('/ui', (c) => {
  return c.html(``);
});

app.get('/resources', async (c) => {
  try {
    const query = c.req.query('query') || '';
    const imageUrl = c.req.query('image_url');
    
    // Validate inputs
    if (!query && !imageUrl) {
      return c.json(
        { error: "Either query or image_url must be provided" },
        400
      );
    }
    
    let imageData: string | undefined;
    let mimeType: string | undefined;
    
    // If image URL is provided, fetch and convert to base64
    if (imageUrl) {
      try {
        const imageResponse = await fetch(imageUrl);
        if (!imageResponse.ok) {
          console.log(`Warning: Could not fetch image from URL: ${imageUrl}`);
        } else {
          const arrayBuffer = await imageResponse.arrayBuffer();
          const uint8Array = new Uint8Array(arrayBuffer);
          imageData = btoa(String.fromCharCode(...uint8Array));
          mimeType = imageResponse.headers.get('content-type') || 'image/png';
        }
      } catch (imageError: any) {
        console.log(`Warning: Error fetching image: ${imageError.message}`);
        // Continue without the image rather than failing
      }
    }
    
    // Call find_resources with proper error handling
    const result = await findResources(query, c.env, imageData, mimeType, c.req.raw.headers);
    return c.json(result);
    
  } catch (error: any) {
    // Log the error
    const errorMsg = `Error processing request: ${error.message}`;
    console.log(errorMsg);
    console.log(error.stack);
    
    // Return a proper error response
    return c.json(
      { error: "Internal server error", message: error.message },
      500
    );
  }
});

// POST endpoint for image uploads (base64 encoded)
app.post('/resources', async (c) => {
  try {
    const body = await c.req.json();
    const { query = '', image_data, mime_type } = body;
    
    // Validate inputs
    if (!query && !image_data) {
      return c.json(
        { error: "Either query or image_data must be provided" },
        400
      );
    }
    
    // Call find_resources with proper error handling
    const result = await findResources(query, c.env, image_data, mime_type, c.req.raw.headers);
    return c.json(result);
    
  } catch (error: any) {
    // Log the error
    const errorMsg = `Error processing request: ${error.message}`;
    console.log(errorMsg);
    console.log(error.stack);
    
    // Return a proper error response
    return c.json(
      { error: "Internal server error", message: error.message },
      500
    );
  }
});

export default app;

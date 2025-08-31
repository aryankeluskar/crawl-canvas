# Canvas Crawler

A powerful AI-powered Canvas LMS resource discovery agent that helps students find relevant educational materials based on their queries or uploaded images.

## Features

- **Intelligent Course Matching**: Uses Google Gemini AI to analyze student queries and match them to relevant courses
- **Module-Level Resource Discovery**: Identifies specific modules within courses that contain relevant materials
- **Multi-modal Input Support**: Accepts both text queries and image uploads for educational content analysis
- **Canvas API Integration**: Directly integrates with Canvas LMS to fetch real course data, modules, and resources
- **Relevance Scoring**: AI-powered scoring system to rank resources by relevance to student queries

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Authentication

#### Canvas API Authentication
You can provide your Canvas API key in two ways:

**Option 1: Environment Variables (recommended for production)**
```bash
wrangler secret put CANVAS_API_KEY
# Enter your Canvas API key when prompted
```

**Option 2: Request Headers (useful for personal access tokens)**
Include one of these headers in your API requests:
- `Authorization: Bearer YOUR_CANVAS_API_KEY`
- `Canvas-API-Key: YOUR_CANVAS_API_KEY`

#### Google Generative AI Configuration  
```bash
wrangler secret put GOOGLE_API_KEY
# Enter your Google API key when prompted
```

### 3. Development

```bash
npm run dev
```

### 4. Deployment

```bash
npm run deploy
```

## API Endpoints

### GET `/`
Health check endpoint that returns API status.

### GET `/resources`
Find educational resources based on a text query or image URL.

**Query Parameters:**
- `query` (string, optional): Text query describing what you're looking for
- `image_url` (string, optional): URL to an educational image to analyze

**Examples:**

Basic query:
```bash
curl "https://canvas-crawler.soyrun.workers.dev/resources?query=matrix%20orthogonalization"
```

With Canvas API key in header:
```bash
curl -H "Authorization: Bearer YOUR_CANVAS_API_KEY" \
     "https://canvas-crawler.soyrun.workers.dev/resources?query=matrix%20orthogonalization"
```

With custom Canvas API key header:
```bash
curl -H "Canvas-API-Key: YOUR_CANVAS_API_KEY" \
     "https://canvas-crawler.soyrun.workers.dev/resources?query=matrix%20orthogonalization"
```

### POST `/resources`
Find educational resources with support for base64-encoded images.

**Request Body:**
```json
{
  "query": "How do matrices work?",
  "image_data": "base64_encoded_image_data",
  "mime_type": "image/png"
}
```

## Response Format

```json
[
  {
    "title": "Matrix Operations Tutorial",
    "type": "Page",
    "url": "https://canvas.asu.edu/courses/.../pages/matrix-ops",
    "course": "Linear Algebra",
    "module": "Matrix Fundamentals", 
    "relevance_score": 0.95
  }
]
```

## Architecture

The application is built using:
- **Hono**: Lightweight web framework for Cloudflare Workers
- **Google Generative AI**: For intelligent query analysis and image processing
- **Canvas LMS API**: For fetching course data and educational resources
- **TypeScript**: For type safety and better development experience

## Configuration

For generating/synchronizing types based on your Worker configuration:

```bash
npm run cf-typegen
```

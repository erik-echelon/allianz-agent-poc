# OpenAI Assistant Chat Frontend

A simple, elegant React frontend for interacting with the OpenAI Assistant API. This application provides a clean interface for uploading documents to a vector store and having conversations with an AI assistant that can reference those documents and search the web when needed.

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Features

- **Elegant Chat Interface**
  - Real-time chat with OpenAI's assistant
  - Markdown rendering for rich responses
  - Message history persisted between sessions
  - Loading indicators for message processing

- **Document Management**
  - Easy file upload with progress tracking
  - Document listing with delete capability
  - Supported file types: PDF, TXT, MD, CSV, JSON

- **Intelligent Web Search**
  - Automatic detection of queries that might need web search
  - No need to explicitly request web searches
  - Seamless integration of document knowledge and web results

- **Responsive Design**
  - Works on desktop and mobile devices
  - Adaptive layout based on screen size


## Installation

### Prerequisites

- Node.js 14+ and npm
- OpenAI Assistant API backend running (see backend README)

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd openai-assistant-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure the backend URL**
   Open `src/utils/api.js` and update the `API_BASE_URL` constant:
   ```javascript
   const API_BASE_URL = 'http://localhost:8000'; // Change if your backend is at a different URL
   ```

4. **Start the development server**
   ```bash
   npm start
   ```

5. **Access the application**
   Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

### Uploading Documents

1. In the sidebar, click "Choose File" to select a document from your computer
2. After selecting a file, click the "Upload" button
3. Wait for the upload to complete (progress bar will show status)
4. Once uploaded, the document will appear in the Documents section

### Chatting with the Assistant

1. Type your message in the input field at the bottom of the chat area
2. Press Enter or click the send button (paper airplane icon)
3. The assistant will respond, potentially referencing your uploaded documents
4. For questions about current events or information not in your documents, the assistant will automatically search the web

### Managing Documents

1. View all uploaded documents in the Documents section of the sidebar
2. To delete a document, click the trash icon next to its name
3. Successful deletion will be confirmed in the chat

## Project Structure

```
openai-assistant-frontend/
├── public/                     # Static files
├── src/
│   ├── components/             # React components organized by feature
│   │   ├── Chat/               # Chat-related components
│   │   ├── Documents/          # Document listing components
│   │   ├── FileUpload/         # File upload components
│   │   └── Sidebar/            # Sidebar components
│   ├── styles/                 # Styled components organized by feature
│   ├── utils/                  # Utility functions and API calls
│   ├── App.js                  # Main application component
│   ├── index.js                # Entry point
│   └── index.css               # Global CSS
└── package.json                # Dependencies and scripts
```

## Configuration

### Backend URL

The application connects to your OpenAI Assistant API backend. By default, it expects the backend to be running at `http://localhost:8000`. To change this:

1. Open `src/utils/api.js`
2. Update the `API_BASE_URL` constant to your backend URL
   ```javascript
   const API_BASE_URL = 'https://your-backend-url.com';
   ```

### Web Search Detection

The application uses heuristics to determine when to enable web search. These can be customized in `src/utils/webSearchDetection.js`:

```javascript
// Add or modify trigger words that indicate web search might be needed
const webSearchTriggers = [
  'current', 'latest', 'recent', 'today', 'news', 'update',
  // Add your custom triggers here
];
```

## Development

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App

### Adding New Features

1. **New Component**:
   - Create a new folder in `src/components/`
   - Add component files and an `index.js` export
   - Add styles in `src/styles/`

2. **Extending API**:
   - Add new API functions in `src/utils/api.js`

### Styling

The application uses styled-components for styling. To modify the look and feel:

1. Check the corresponding style file in `src/styles/`
2. Update the styled component definitions

## Troubleshooting

### Common Issues

1. **Backend Connection Fails**
   - Ensure your backend is running
   - Check that the `API_BASE_URL` is correct
   - Verify CORS is properly configured on the backend

2. **Document Upload Fails**
   - Check that the file type is supported
   - Ensure the file size is within limits (typically <512MB)
   - Look for detailed error messages in the browser console

3. **Chat History Issues**
   - If chat history isn't saving, check your browser's localStorage settings
   - Clear localStorage with `localStorage.removeItem('chatMessages')` in the console

### Getting Help

If you encounter issues:

1. Check the browser console for error messages
2. Review the backend logs for API errors
3. Ensure all dependencies are correctly installed
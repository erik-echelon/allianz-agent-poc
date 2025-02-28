import React, { useState, useEffect } from 'react';
import { 
  AppContainer, 
  Header, 
  MainContent 
} from './styles/GlobalStyles';
import Sidebar from './components/Sidebar';
import ChatContainer from './components/Chat';
import { fetchDocuments, sendMessage, deleteDocument } from './utils/api';
import { needsWebSearch } from './utils/webSearchDetection';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState([]);

  // Load chat history from localStorage on initial load
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
    
    // Fetch documents on load
    loadDocuments();
  }, []);

  // Save messages to localStorage when they change
  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages));
  }, [messages]);

  // Fetch documents from API
  const loadDocuments = async () => {
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  // Handle sending message
  const handleSendMessage = async () => {
    if (inputMessage.trim() === '') return;
    
    // Add user message to chat
    const userMessage = { role: 'user', content: inputMessage };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Determine if this query likely needs web search
      const searchWeb = needsWebSearch(inputMessage);
      
      // Send request to API
      const response = await sendMessage([...messages, userMessage], searchWeb);

      // Add assistant response to chat
      setMessages(prevMessages => [
        ...prevMessages, 
        { role: 'assistant', content: response.content }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prevMessages => [
        ...prevMessages,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = (response, fileName) => {
    // Refresh documents list
    loadDocuments();
    
    // Add system message about successful upload
    setMessages(prevMessages => [
      ...prevMessages,
      { 
        role: 'assistant', 
        content: `File "${fileName}" has been uploaded successfully. You can now ask questions about its content.` 
      }
    ]);
  };

  // Handle document deletion
  const handleDocumentDelete = async (documentId) => {
    try {
      await deleteDocument(documentId);
      
      // Update documents list
      setDocuments(prevDocuments => 
        prevDocuments.filter(doc => doc.document_id !== documentId)
      );
      
      // Add system message about successful deletion
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          role: 'assistant', 
          content: 'Document has been deleted successfully.' 
        }
      ]);
    } catch (error) {
      console.error('Error deleting document:', error);
      setMessages(prevMessages => [
        ...prevMessages,
        { 
          role: 'assistant', 
          content: 'Error deleting document. Please try again.' 
        }
      ]);
    }
  };

  return (
    <AppContainer>
      <Header>OpenAI Assistant Chat</Header>
      
      <MainContent>
        <Sidebar 
          documents={documents}
          onDocumentDelete={handleDocumentDelete}
          onFileUpload={handleFileUpload}
        />
        
        <ChatContainer 
          messages={messages}
          inputMessage={inputMessage}
          setInputMessage={setInputMessage}
          handleSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </MainContent>
    </AppContainer>
  );
};

export default App;
import React, { useRef, useEffect } from 'react';
import { 
  ChatContainer as ChatContainerStyled, 
  MessageList, 
  WelcomeMessage,
  LoadingDots
} from '../../styles/ChatStyles';
import MessageItem from './MessageItem';
import MessageInput from './MessageInput';

const ChatContainer = ({ 
  messages, 
  inputMessage, 
  setInputMessage, 
  handleSendMessage, 
  isLoading 
}) => {
  const chatContainerRef = useRef(null);
  const messageEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <ChatContainerStyled ref={chatContainerRef}>
      <MessageList>
        {messages.length === 0 ? (
          <WelcomeMessage>
            <h2>Welcome to OpenAI Assistant Chat!</h2>
            <p>Upload documents and start asking questions.</p>
            <p>The assistant will automatically search the web when needed.</p>
          </WelcomeMessage>
        ) : (
          messages.map((message, index) => (
            <MessageItem key={index} message={message} />
          ))
        )}
        
        {isLoading && (
          <MessageItem
            message={{
              role: 'assistant',
              content: <LoadingDots><div></div><div></div><div></div></LoadingDots>
            }}
          />
        )}
        <div ref={messageEndRef} />
      </MessageList>
      
      <MessageInput
        inputMessage={inputMessage}
        setInputMessage={setInputMessage}
        handleSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </ChatContainerStyled>
  );
};

export default ChatContainer;
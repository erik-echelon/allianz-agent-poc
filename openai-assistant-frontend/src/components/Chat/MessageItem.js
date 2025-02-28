import React from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  MessageItem as MessageItemContainer, 
  MessageRole, 
  MessageContent 
} from '../../styles/ChatStyles';

const MessageItem = ({ message }) => {
  const roleLabel = message.role === 'user' ? 'You' : 'Assistant';
  
  return (
    <MessageItemContainer className={message.role}>
      <MessageRole>{roleLabel}</MessageRole>
      <MessageContent>
        <ReactMarkdown>
          {message.content}
        </ReactMarkdown>
      </MessageContent>
    </MessageItemContainer>
  );
};

export default MessageItem;
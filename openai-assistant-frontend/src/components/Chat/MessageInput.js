import React from 'react';
import { FaPaperPlane } from 'react-icons/fa';
import { 
  InputContainer, 
  MessageInputField, 
  SendButton 
} from '../../styles/ChatStyles';

const MessageInput = ({ inputMessage, setInputMessage, handleSendMessage, isLoading }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <InputContainer>
      <MessageInputField
        value={inputMessage}
        onChange={(e) => setInputMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Type your message here..."
        disabled={isLoading}
      />
      <SendButton 
        onClick={handleSendMessage} 
        disabled={isLoading || inputMessage.trim() === ''}
      >
        <FaPaperPlane />
      </SendButton>
    </InputContainer>
  );
};

export default MessageInput;
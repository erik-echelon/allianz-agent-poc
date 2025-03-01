import styled from 'styled-components';

export const LoadingDots = styled.div`
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  
  div {
    width: 8px;
    height: 8px;
    background-color: #999;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
  }
  
  div:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  div:nth-child(2) {
    animation-delay: -0.16s;
  }
  
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
`;

export const WelcomeMessage = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
  padding: 2rem;
  
  h2 {
    color: #0066cc;
    margin-bottom: 1rem;
  }
  
  p {
    margin: 0.5rem 0;
  }
`;

export const ChatContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
`;

export const MessageList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

export const MessageItem = styled.div`
  display: flex;
  flex-direction: column;
  max-width: 70%;
  
  &.user {
    align-self: flex-end;
  }
  
  &.assistant {
    align-self: flex-start;
  }
`;

export const MessageRole = styled.div`
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 0.2rem;
  padding: 0 0.5rem;
  
  .user & {
    align-self: flex-end;
  }
`;

export const MessageContent = styled.div`
  padding: 0.8rem 1rem;
  white-space: pre-wrap;
  word-break: break-word;
  
  .user & {
    background-color: #0066cc;
    color: white;
    border-radius: 18px 18px 4px 18px;
  }
  
  .assistant & {
    background-color: #f0f0f0;
    color: #333;
    border-radius: 18px 18px 18px 4px;
  }
  
  p {
    margin: 0.5rem 0;
    &:first-child {
      margin-top: 0;
    }
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  a {
    color: inherit;
    text-decoration: underline;
  }
  
  code {
    font-family: monospace;
    padding: 0.1rem 0.3rem;
    background-color: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
  }
  
  pre {
    background-color: rgba(0, 0, 0, 0.1);
    padding: 0.5rem;
    border-radius: 4px;
    overflow-x: auto;
    
    code {
      background: none;
      padding: 0;
    }
  }
`;

export const InputContainer = styled.div`
  display: flex;
  padding: 1rem;
  background-color: #f5f5f5;
  border-top: 1px solid #ddd;
`;

export const MessageInputField = styled.input`
  flex: 1;
  padding: 0.8rem 1rem;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: #0066cc;
  }
  
  &:disabled {
    background-color: #f9f9f9;
    cursor: not-allowed;
  }
`;

export const SendButton = styled.button`
  padding: 0.8rem;
  background-color: #0066cc;
  color: white;
  border: none;
  border-radius: 50%;
  margin-left: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover:not(:disabled) {
    background-color: #0055aa;
  }
  
  &:disabled {
    background-color: #99ccff;
    cursor: not-allowed;
  }
`;
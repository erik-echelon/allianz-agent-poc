import styled from 'styled-components';

export const FileInputWrapper = styled.div`
  margin-bottom: 1rem;
`;

export const FileInput = styled.input`
  display: none;
`;

export const FileInputLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  
  &:hover {
    background-color: #e0e0e0;
  }
`;

export const UploadButton = styled.button`
  padding: 0.5rem 1rem;
  background-color: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
  font-size: 0.9rem;
  
  &:hover:not(:disabled) {
    background-color: #0055aa;
  }
  
  &:disabled {
    background-color: #99ccff;
    cursor: not-allowed;
  }
  
  .spinner {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export const ProgressBarContainer = styled.div`
  width: 100%;
  height: 5px;
  background-color: #e0e0e0;
  border-radius: 3px;
  margin-top: 0.5rem;
  overflow: hidden;
`;

export const ProgressBarFill = styled.div`
  height: 100%;
  width: ${props => props.width}%;
  background-color: #0066cc;
  transition: width 0.3s ease;
`;
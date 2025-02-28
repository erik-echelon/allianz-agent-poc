import styled from 'styled-components';

export const DocumentList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

export const EmptyDocuments = styled.div`
  color: #999;
  font-style: italic;
  font-size: 0.9rem;
`;

export const DocumentItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
`;

export const DocumentName = styled.div`
  font-size: 0.9rem;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-right: 0.5rem;
`;

export const DeleteButton = styled.button`
  background: none;
  border: none;
  color: #ff3333;
  cursor: pointer;
  font-size: 0.8rem;
  
  &:hover {
    color: #cc0000;
  }
`;
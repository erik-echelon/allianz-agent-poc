import styled from 'styled-components';

export const Sidebar = styled.div`
  width: 300px;
  background-color: #f5f5f5;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  overflow-y: auto;
  
  @media (max-width: 768px) {
    width: 100%;
    max-height: 300px;
    border-right: none;
    border-bottom: 1px solid #ddd;
  }
`;

export const SidebarSectionContainer = styled.div`
  margin-bottom: 2rem;
`;

export const SidebarTitle = styled.h3`
  margin-top: 0;
  margin-bottom: 1rem;
  color: #333;
  font-size: 1.1rem;
`;
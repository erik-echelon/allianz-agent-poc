import styled from 'styled-components';

export const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
`;

export const Header = styled.header`
  background-color: #0066cc;
  color: white;
  padding: 1rem;
  text-align: center;
  font-size: 1.5rem;
  font-weight: bold;
`;

export const MainContent = styled.main`
  display: flex;
  flex: 1;
  overflow: hidden;
  
  @media (max-width: 768px) {
    flex-direction: column;
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
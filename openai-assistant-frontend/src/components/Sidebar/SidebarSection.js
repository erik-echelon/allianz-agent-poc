import React from 'react';
import { SidebarSectionContainer, SidebarTitle } from '../../styles/SidebarStyles';

const SidebarSection = ({ title, children }) => {
  return (
    <SidebarSectionContainer>
      <SidebarTitle>{title}</SidebarTitle>
      {children}
    </SidebarSectionContainer>
  );
};

export default SidebarSection;
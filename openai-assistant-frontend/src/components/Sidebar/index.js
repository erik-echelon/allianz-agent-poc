import React from 'react';
import { Sidebar as SidebarContainer } from '../../styles/SidebarStyles';
import SidebarSection from './SidebarSection';
import FileUpload from '../FileUpload';
import DocumentList from '../Documents';

const Sidebar = ({ documents, onDocumentDelete, onFileUpload }) => {
  return (
    <SidebarContainer>
      <SidebarSection title="Upload Document">
        <FileUpload onFileUpload={onFileUpload} />
      </SidebarSection>
      
      <SidebarSection title="Documents">
        <DocumentList 
          documents={documents} 
          onDocumentDelete={onDocumentDelete} 
        />
      </SidebarSection>
    </SidebarContainer>
  );
};

export default Sidebar;
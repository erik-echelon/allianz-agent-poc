import React from 'react';
import { DocumentList as DocumentListContainer, EmptyDocuments } from '../../styles/DocumentStyles';
import DocumentItem from './DocumentItem';

const DocumentList = ({ documents, onDocumentDelete }) => {
  if (!documents || documents.length === 0) {
    return <EmptyDocuments>No documents uploaded yet</EmptyDocuments>;
  }

  return (
    <DocumentListContainer>
      {documents.map(doc => (
        <DocumentItem 
          key={doc.document_id} 
          document={doc} 
          onDelete={onDocumentDelete} 
        />
      ))}
    </DocumentListContainer>
  );
};

export default DocumentList;
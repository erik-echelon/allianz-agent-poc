import React from 'react';
import { FaTrash } from 'react-icons/fa';
import { 
  DocumentItem as DocumentItemContainer, 
  DocumentName, 
  DeleteButton 
} from '../../styles/DocumentStyles';

const DocumentItem = ({ document, onDelete }) => {
  const handleDelete = () => {
    if (onDelete) {
      onDelete(document.document_id);
    }
  };

  return (
    <DocumentItemContainer>
      <DocumentName>{document.filename}</DocumentName>
      <DeleteButton onClick={handleDelete}>
        <FaTrash />
      </DeleteButton>
    </DocumentItemContainer>
  );
};

export default DocumentItem;
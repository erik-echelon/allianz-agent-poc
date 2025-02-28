import React from 'react';
import { FaFile } from 'react-icons/fa';
import { 
  FileInputWrapper, 
  FileInput as StyledFileInput,
  FileInputLabel
} from '../../styles/FileUploadStyles';

const FileInput = ({ selectedFile, onFileChange, isUploading }) => {
  return (
    <FileInputWrapper>
      <StyledFileInput 
        type="file" 
        id="fileInput" 
        onChange={onFileChange} 
        disabled={isUploading}
      />
      <FileInputLabel htmlFor="fileInput">
        <FaFile /> {selectedFile ? selectedFile.name : 'Choose File'}
      </FileInputLabel>
    </FileInputWrapper>
  );
};

export default FileInput;
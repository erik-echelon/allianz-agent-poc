import React, { useState } from 'react';
import { FaSpinner } from 'react-icons/fa';
import { UploadButton } from '../../styles/FileUploadStyles';
import FileInput from './FileInput';
import ProgressBar from './ProgressBar';
import { uploadDocument } from '../../utils/api';

const FileUpload = ({ onFileUpload }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      // Upload the file and track progress
      const response = await uploadDocument(
        selectedFile, 
        (progress) => setUploadProgress(progress)
      );
      
      // Notify parent component of successful upload
      if (onFileUpload) {
        onFileUpload(response, selectedFile.name);
      }
      
      // Reset file selection
      setSelectedFile(null);
      
    } catch (error) {
      console.error('Error uploading file:', error);
      // Error handling could be added here
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <>
      <FileInput 
        selectedFile={selectedFile}
        onFileChange={handleFileChange}
        isUploading={isUploading}
      />
      
      {selectedFile && (
        <UploadButton onClick={handleUpload} disabled={isUploading}>
          {isUploading ? <FaSpinner className="spinner" /> : 'Upload'}
        </UploadButton>
      )}
      
      {isUploading && <ProgressBar progress={uploadProgress} />}
    </>
  );
};

export default FileUpload;
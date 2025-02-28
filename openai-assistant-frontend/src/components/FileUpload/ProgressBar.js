import React from 'react';
import { 
  ProgressBarContainer, 
  ProgressBarFill 
} from '../../styles/FileUploadStyles';

const ProgressBar = ({ progress }) => {
  return (
    <ProgressBarContainer>
      <ProgressBarFill width={progress} />
    </ProgressBarContainer>
  );
};

export default ProgressBar;
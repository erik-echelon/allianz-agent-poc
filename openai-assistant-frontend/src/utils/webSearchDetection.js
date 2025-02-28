/**
 * Determines if a message likely needs web search based on content analysis
 */
export const needsWebSearch = (message) => {
    const webSearchTriggers = [
      'current', 'latest', 'recent', 'today', 'news', 'update',
      'what is happening', 'developments', 'trend', 'weather',
      'stock', 'price', 'market', 'comparison', 'versus', 'vs',
      'outside', 'online', 'web', 'internet', 'search'
    ];
    
    const lowerMessage = message.toLowerCase();
    
    // Check if message contains time references
    const hasTimeReference = /today|now|current|latest|recent|this (week|month|year)/.test(lowerMessage);
    
    // Check if message contains any trigger words
    const hasTriggerWord = webSearchTriggers.some(trigger => lowerMessage.includes(trigger));
    
    // Check if message appears to be about external information
    const isQuestionAboutWorld = /what|who|when|where|why|how/.test(lowerMessage) && 
      !lowerMessage.includes('document') && !lowerMessage.includes('file');
      
    return hasTimeReference || hasTriggerWord || isQuestionAboutWorld;
  };
// ResponseStyleService.js
// Manages user response style preferences for AI interactions

const RESPONSE_STYLES = {
  concise: {
    name: 'Concise',
    description: 'Brief and to-the-point responses',
    systemPrompt: `You should provide concise, brief responses. Get straight to the point without unnecessary elaboration. 
Keep answers short (2-4 sentences typically) unless the question explicitly requires more detail.
Avoid long explanations, examples, or tangents unless specifically requested.`,
    maxTokens: 800,
    temperature: 0.7,
  },
  balanced: {
    name: 'Balanced',
    description: 'Well-rounded responses with moderate detail',
    systemPrompt: `You should provide balanced responses with appropriate detail. 
Include relevant context and examples when helpful, but avoid being overly verbose.
Aim for clear, informative answers that are neither too brief nor too lengthy (typically 4-8 sentences).`,
    maxTokens: 1500,
    temperature: 0.7,
  },
  detailed: {
    name: 'Detailed',
    description: 'Comprehensive and thorough responses',
    systemPrompt: `You should provide detailed, comprehensive responses with thorough explanations.
Include relevant context, examples, step-by-step breakdowns, and additional insights.
Explore multiple angles and provide in-depth analysis when appropriate.
Use formatting like bullet points or numbered lists when it helps clarity.`,
    maxTokens: 2500,
    temperature: 0.7,
  }
};

class ResponseStyleService {
  constructor() {
    this.currentStyle = this.loadStyleFromStorage();
  }

  /**
   * Load the user's response style preference from localStorage
   */
  loadStyleFromStorage() {
    try {
      const saved = localStorage.getItem('response_style');
      return saved && RESPONSE_STYLES[saved] ? saved : 'balanced';
    } catch (error) {
      console.error('Failed to load response style:', error);
      return 'balanced';
    }
  }

  /**
   * Save the user's response style preference to localStorage
   */
  saveStyleToStorage(style) {
    try {
      if (!RESPONSE_STYLES[style]) {
        throw new Error(`Invalid style: ${style}`);
      }
      localStorage.setItem('response_style', style);
      this.currentStyle = style;
      return true;
    } catch (error) {
      console.error('Failed to save response style:', error);
      return false;
    }
  }

  /**
   * Get the current response style
   */
  getCurrentStyle() {
    return this.currentStyle;
  }

  /**
   * Set the current response style
   */
  setStyle(style) {
    if (!RESPONSE_STYLES[style]) {
      console.error(`Invalid style: ${style}`);
      return false;
    }
    this.currentStyle = style;
    return this.saveStyleToStorage(style);
  }

  /**
   * Get the configuration for the current style
   */
  getStyleConfig() {
    return RESPONSE_STYLES[this.currentStyle];
  }

  /**
   * Get the system prompt for the current style
   */
  getSystemPrompt() {
    return RESPONSE_STYLES[this.currentStyle].systemPrompt;
  }

  /**
   * Get the max tokens for the current style
   */
  getMaxTokens() {
    return RESPONSE_STYLES[this.currentStyle].maxTokens;
  }

  /**
   * Get the temperature for the current style
   */
  getTemperature() {
    return RESPONSE_STYLES[this.currentStyle].temperature;
  }

  /**
   * Get all available styles
   */
  getAllStyles() {
    return RESPONSE_STYLES;
  }

  /**
   * Format the style parameters for API request
   */
  getAPIParams() {
    const config = this.getStyleConfig();
    return {
      style: this.currentStyle,
      systemPrompt: config.systemPrompt,
      maxTokens: config.maxTokens,
      temperature: config.temperature,
    };
  }

  /**
   * Override style temporarily for specific queries
   * (e.g., force detailed for math/coding questions)
   */
  getStyleForQuery(query) {
    const lowerQuery = query.toLowerCase();
    
    // Force detailed style for complex questions
    if (
      lowerQuery.includes('explain in detail') ||
      lowerQuery.includes('elaborate') ||
      lowerQuery.includes('comprehensive') ||
      lowerQuery.includes('step by step')
    ) {
      return 'detailed';
    }
    
    // Force concise style for simple questions
    if (
      lowerQuery.includes('briefly') ||
      lowerQuery.includes('in short') ||
      lowerQuery.includes('quick answer') ||
      lowerQuery.includes('tldr')
    ) {
      return 'concise';
    }
    
    // Return current style for normal queries
    return this.currentStyle;
  }
}

// Create a singleton instance
const responseStyleService = new ResponseStyleService();

// Export for use in other modules
export default responseStyleService;

// Also export the service class for testing
export { ResponseStyleService, RESPONSE_STYLES };
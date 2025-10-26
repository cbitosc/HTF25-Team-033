import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader, User, Bot, Copy, Check, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const ChatInterface = ({ selectedDocuments, onAsk }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load initial suggestions when documents are selected
    if (selectedDocuments.length > 0) {
      loadSuggestions();
    }
  }, [selectedDocuments]);

  const loadSuggestions = async () => {
    try {
      const { getQuestionSuggestions } = await import('../lib/api');
      const result = await getQuestionSuggestions(selectedDocuments[0].doc_id);
      setSuggestions(result.suggestions);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const handleSubmit = async (e, questionText = null) => {
    e?.preventDefault();
    
    const question = questionText || input;
    if (!question.trim() || loading) return;

    // Add user message
    const userMessage = {
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const { askQuestion } = await import('../lib/api');
      const docIds = selectedDocuments.map(doc => doc.doc_id);
      
      // Build conversation history
      const history = messages.map(msg => ({
        question: msg.role === 'user' ? msg.content : '',
        answer: msg.role === 'assistant' ? msg.content : ''
      })).filter(item => item.question || item.answer);

      const response = await onAsk(question, docIds, history);

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        confidence: response.confidence_score,
        suggestedQuestions: response.suggested_questions,
        processingTime: response.processing_time,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setSuggestions(response.suggested_questions);
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        error: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    handleSubmit(null, suggestion);
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (selectedDocuments.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 
                     flex items-center justify-center"
          >
            <Bot className="w-12 h-12 text-primary" />
          </motion.div>
          <h3 className="text-2xl font-bold mb-2 gradient-text">
            Select a Document
          </h3>
          <p className="text-gray-400">
            Choose one or more documents to start asking questions
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="glass rounded-t-xl p-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary 
                        flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold">AI Assistant</h3>
            <p className="text-sm text-gray-400">
              {selectedDocuments.length} document{selectedDocuments.length > 1 ? 's' : ''} selected
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary 
                              flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}

              <div className={`flex-1 max-w-3xl ${message.role === 'user' ? 'text-right' : ''}`}>
                <div
                  className={`
                    inline-block rounded-2xl p-4 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-primary to-secondary text-white'
                        : message.error
                        ? 'glass border border-red-500/20 text-red-400'
                        : 'glass'
                    }
                  `}
                >
                  {/* Answer Type Badge for AI responses */}
                  {message.role === 'assistant' && !message.error && message.answer_type === 'hybrid' && (
                    <div className="mb-3 inline-flex items-center gap-2 px-3 py-1 rounded-full 
                                  bg-gradient-to-r from-purple-500/20 to-blue-500/20 
                                  border border-purple-500/30 text-xs">
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></span>
                      <span className="text-purple-300 font-medium">
                        Answer enhanced with general knowledge
                      </span>
                    </div>
                  )}
                  
                  {message.role === 'assistant' ? (
                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>

                {/* Assistant Message Footer */}
                {message.role === 'assistant' && !message.error && (
                  <div className="mt-3 space-y-3">
                    {/* Confidence & Time */}
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <span>
                        Confidence: <span className="text-primary font-semibold">
                          {(message.confidence * 100).toFixed(0)}%
                        </span>
                      </span>
                      <span>•</span>
                      <span>{message.processingTime}s</span>
                      <button
                        onClick={() => copyToClipboard(message.content, index)}
                        className="ml-auto p-1 hover:text-primary transition-colors"
                      >
                        {copiedIndex === index ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    {/* Citations */}
                    {/* Citations */}
                    {message.citations && message.citations.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-400 flex items-center gap-2">
                          <ExternalLink className="w-3 h-3" />
                          Sources Referenced:
                        </p>
                        <div className="grid grid-cols-1 gap-2">
                          {message.citations.map((citation, cidx) => (
                            <motion.div
                              key={cidx}
                              whileHover={{ scale: 1.02, x: 5 }}
                              className="glass rounded-lg p-3 text-xs cursor-pointer hover:border-primary/50 
                                      border border-gray-700 transition-all"
                            >
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-8 h-8 rounded bg-primary/20 flex items-center justify-center">
                                  <span className="text-primary font-bold">{cidx + 1}</span>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="font-semibold text-primary">
                                      Page {citation.page_number}
                                    </span>
                                    <span className="text-gray-500">•</span>
                                    <span className="text-gray-400">
                                      Confidence: {(citation.confidence * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <p className="text-gray-300 leading-relaxed line-clamp-2">
                                    {citation.text}
                                  </p>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Suggested Questions */}
                    {message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-400">Follow-up questions:</p>
                        <div className="space-y-2">
                          {message.suggestedQuestions.map((question, qidx) => (
                            <motion.button
                              key={qidx}
                              whileHover={{ scale: 1.02 }}
                              onClick={() => handleSuggestionClick(question)}
                              className="w-full text-left glass rounded-lg p-3 text-sm hover:border-primary/50 
                                       border border-transparent transition-all"
                            >
                              {question}
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-4"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary 
                          flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="glass rounded-2xl p-4">
              <div className="flex gap-2">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                  className="w-2 h-2 bg-primary rounded-full"
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                  className="w-2 h-2 bg-primary rounded-full"
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                  className="w-2 h-2 bg-primary rounded-full"
                />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="glass rounded-b-xl p-4 border-t border-gray-800">
        {/* Quick Suggestions */}
        {messages.length === 0 && suggestions.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-400 mb-2">Suggested questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, idx) => (
                <motion.button
                  key={idx}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-3 py-1.5 rounded-lg glass text-sm hover:border-primary/50 
                           border border-transparent transition-all"
                >
                  {suggestion}
                </motion.button>
              ))}
            </div>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={loading}
            className="flex-1 bg-gray-900 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 
                     focus:ring-primary border border-gray-800 disabled:opacity-50"
          />
          <motion.button
            type="submit"
            disabled={!input.trim() || loading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-secondary 
                     text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed
                     hover:shadow-lg hover:shadow-primary/50 transition-all"
          >
            {loading ? (
              <Loader className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
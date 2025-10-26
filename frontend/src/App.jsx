import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, MessageSquare, Sparkles, RefreshCw } from 'lucide-react';
import UploadZone from './components/UploadZone';
import DocumentCard from './components/DocumentCard';
import ChatInterface from './components/ChatInterface';
import DocumentDashboard from './components/DocumentDashboard';
import { listDocuments, deleteDocument, askQuestion } from './lib/api';

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'chat'
  const [loading, setLoading] = useState(true);
  const [showToast, setShowToast] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
      showToastMessage('Failed to load documents', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadComplete = (newDoc) => {
    setDocuments(prev => [newDoc, ...prev]);
    showToastMessage('Document uploaded successfully!', 'success');
    
    // Auto-select the new document and switch to chat
    setSelectedDocuments([newDoc]);
    setActiveTab('chat');
  };

  const handleDeleteDocument = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(docId);
      setDocuments(prev => prev.filter(doc => doc.doc_id !== docId));
      setSelectedDocuments(prev => prev.filter(doc => doc.doc_id !== docId));
      showToastMessage('Document deleted', 'success');
    } catch (error) {
      console.error('Failed to delete document:', error);
      showToastMessage('Failed to delete document', 'error');
    }
  };

  const handleSelectDocument = (doc) => {
    setSelectedDocuments(prev => {
      const isSelected = prev.some(d => d.doc_id === doc.doc_id);
      if (isSelected) {
        return prev.filter(d => d.doc_id !== doc.doc_id);
      } else {
        return [...prev, doc];
      }
    });
  };

  const handleAsk = async (question, docIds, history) => {
    return await askQuestion(question, docIds, history);
  };

  const showToastMessage = (message, type = 'info') => {
    setShowToast({ message, type });
    setTimeout(() => setShowToast(null), 3000);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl animate-pulse-slow" 
             style={{ animationDelay: '1s' }} />
      </div>

      {/* Toast Notifications */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="fixed top-4 right-4 z-50"
          >
            <div className={`
              glass rounded-xl p-4 flex items-center gap-3 shadow-lg
              ${showToast.type === 'error' ? 'border-red-500/50' : 'border-green-500/50'}
              border
            `}>
              <div className={`w-2 h-2 rounded-full ${
                showToast.type === 'error' ? 'bg-red-500' : 'bg-green-500'
              }`} />
              <p className="font-medium">{showToast.message}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header className="relative border-b border-gray-800 glass">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-4"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-secondary 
                            flex items-center justify-center">
                <Sparkles className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold gradient-text">
                  DocuMind AI
                </h1>
                <p className="text-sm text-gray-400">
                  Intelligent Document Question Answering
                </p>
              </div>
            </motion.div>

            <motion.button
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={loadDocuments}
              disabled={loading}
              className="p-3 rounded-xl glass hover:border-primary/50 border border-transparent 
                       transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </motion.button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-4 mb-8">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('upload')}
            className={`
              flex-1 py-4 rounded-xl font-semibold transition-all
              ${activeTab === 'upload'
                ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg shadow-primary/30'
                : 'glass hover:border-gray-700'
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <FileText className="w-5 h-5" />
              <span>Documents</span>
              {documents.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-white/20 text-xs">
                  {documents.length}
                </span>
              )}
            </div>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('chat')}
            className={`
              flex-1 py-4 rounded-xl font-semibold transition-all
              ${activeTab === 'chat'
                ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg shadow-primary/30'
                : 'glass hover:border-gray-700'
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <MessageSquare className="w-5 h-5" />
              <span>Chat</span>
              {selectedDocuments.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-white/20 text-xs">
                  {selectedDocuments.length}
                </span>
              )}
            </div>
          </motion.button>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'upload' ? (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Upload Zone */}
              <div className="mb-12">
                <UploadZone onUploadComplete={handleUploadComplete} />
              </div>

              {/* Dashboard */}
              {documents.length > 0 && (
                <>
                  <DocumentDashboard documents={documents} />

                  {/* Documents Grid */}
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold">Your Documents</h2>
                      <p className="text-sm text-gray-400">
                        Click to select for Q&A
                      </p>
                    </div>

                    {loading ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                          <div key={i} className="glass rounded-xl p-6 animate-pulse">
                            <div className="h-6 bg-gray-800 rounded mb-4" />
                            <div className="h-4 bg-gray-800 rounded mb-2" />
                            <div className="h-4 bg-gray-800 rounded w-2/3" />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {documents.map(doc => (
                          <DocumentCard
                            key={doc.doc_id}
                            document={doc}
                            onDelete={handleDeleteDocument}
                            onSelect={handleSelectDocument}
                            isSelected={selectedDocuments.some(d => d.doc_id === doc.doc_id)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Empty State */}
              {!loading && documents.length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-20"
                >
                  <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 
                                flex items-center justify-center">
                    <FileText className="w-12 h-12 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2 gradient-text">
                    No documents yet
                  </h3>
                  <p className="text-gray-400">
                    Upload your first document to get started
                  </p>
                </motion.div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="h-[calc(100vh-280px)]"
            >
              {/* Selected Documents Bar */}
              {selectedDocuments.length > 0 && (
                <div className="glass rounded-xl p-4 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400 mb-2">Selected Documents:</p>
                      <div className="flex flex-wrap gap-2">
                        {selectedDocuments.map(doc => (
                          <div
                            key={doc.doc_id}
                            className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-sm 
                                     border border-primary/30 flex items-center gap-2"
                          >
                            <FileText className="w-4 h-4" />
                            <span className="font-medium">{doc.filename}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => setActiveTab('upload')}
                      className="px-4 py-2 rounded-lg glass hover:border-primary/50 text-sm 
                               transition-all"
                    >
                      Change Selection
                    </button>
                  </div>
                </div>
              )}

              {/* Chat Interface */}
              <div className="glass rounded-xl h-full overflow-hidden">
                <ChatInterface
                  selectedDocuments={selectedDocuments}
                  onAsk={handleAsk}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="relative border-t border-gray-800 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <p>Built with ❤️ for the Hackathon</p>
            <div className="flex items-center gap-4">
              <span>Powered by Gemini 1.5 Flash</span>
              <span>•</span>
              <span>FastAPI + React</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
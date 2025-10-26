import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, Loader } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const UploadZone = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  }, []);

  const handleFileSelection = (file) => {
    // Validate file type
    const validTypes = ['application/pdf', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      setError('Only PDF and TXT files are supported');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setError(null);
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const { uploadDocument } = await import('../lib/api');
      const result = await uploadDocument(selectedFile, setProgress);
      
      // Success animation
      setProgress(100);
      setTimeout(() => {
        onUploadComplete(result);
        setSelectedFile(null);
        setUploading(false);
        setProgress(0);
      }, 500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
      setProgress(0);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setError(null);
    setProgress(0);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Upload Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative overflow-hidden rounded-2xl border-2 border-dashed
            transition-all duration-300 cursor-pointer
            ${isDragging 
              ? 'border-primary bg-primary/10 scale-105' 
              : 'border-gray-700 hover:border-gray-600 glass'
            }
            ${selectedFile ? 'border-secondary' : ''}
          `}
        >
          {/* Animated Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5 animate-gradient" 
               style={{ backgroundSize: '200% 200%' }} />
          
          <input
            type="file"
            onChange={handleFileInput}
            accept=".pdf,.txt"
            className="hidden"
            id="file-input"
            disabled={uploading}
          />

          <label
            htmlFor="file-input"
            className="relative block p-12 text-center cursor-pointer"
          >
            <AnimatePresence mode="wait">
              {!selectedFile ? (
                <motion.div
                  key="upload"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="mx-auto w-20 h-20 mb-6 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center"
                  >
                    <Upload className="w-10 h-10 text-white" />
                  </motion.div>

                  <h3 className="text-2xl font-bold mb-2 gradient-text">
                    Drop your document here
                  </h3>
                  <p className="text-gray-400 mb-4">
                    or click to browse
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports PDF and TXT files up to 10MB
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="selected"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="space-y-4"
                >
                  <div className="flex items-center justify-center gap-4">
                    <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                      <File className="w-8 h-8 text-primary" />
                    </div>
                    
                    <div className="flex-1 text-left">
                      <h4 className="font-semibold text-lg truncate max-w-md">
                        {selectedFile.name}
                      </h4>
                      <p className="text-sm text-gray-400">
                        {(selectedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>

                    {!uploading && (
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          clearSelection();
                        }}
                        className="p-2 rounded-full hover:bg-red-500/20 transition-colors"
                      >
                        <X className="w-5 h-5 text-red-400" />
                      </button>
                    )}
                  </div>

                  {/* Progress Bar */}
                  {uploading && (
                    <div className="space-y-2">
                      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${progress}%` }}
                          className="h-full bg-gradient-to-r from-primary to-secondary"
                        />
                      </div>
                      <p className="text-sm text-gray-400">
                        {progress < 100 ? `Uploading... ${progress}%` : 'Processing...'}
                      </p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </label>
        </div>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload Button */}
        {selectedFile && !uploading && !error && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={handleUpload}
            className="mt-6 w-full py-4 rounded-xl bg-gradient-to-r from-primary to-secondary 
                     text-white font-semibold text-lg hover:shadow-lg hover:shadow-primary/50 
                     transition-all duration-300 hover:scale-105"
          >
            Upload & Process Document
          </motion.button>
        )}
      </motion.div>
    </div>
  );
};

export default UploadZone;
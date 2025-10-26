import { motion } from 'framer-motion';
import { File, Calendar, Hash, Clock, Brain, Trash2, BarChart } from 'lucide-react';
import { useState } from 'react';

const DocumentCard = ({ document, onDelete, onSelect, isSelected }) => {
  const [showDetails, setShowDetails] = useState(false);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.02 }}
      className={`
        relative glass rounded-xl p-6 cursor-pointer transition-all duration-300
        ${isSelected ? 'ring-2 ring-primary shadow-lg shadow-primary/20' : 'hover:shadow-lg'}
      `}
      onClick={() => onSelect(document)}
    >
      {/* Selection Indicator */}
      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-2 -right-2 w-8 h-8 bg-primary rounded-full flex items-center justify-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 0.5 }}
          >
            ✓
          </motion.div>
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 
                        flex items-center justify-center flex-shrink-0">
            <File className="w-6 h-6 text-primary" />
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg truncate mb-1">
              {document.filename}
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(document.upload_time)}</span>
            </div>
          </div>
        </div>

        {/* Delete Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(document.doc_id);
          }}
          className="p-2 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 
                   transition-colors"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="glass rounded-lg p-3">
          <div className="flex items-center gap-2 text-gray-400 mb-1">
            <Hash className="w-4 h-4" />
            <span className="text-xs">Pages</span>
          </div>
          <p className="text-xl font-bold">{document.total_pages}</p>
        </div>

        <div className="glass rounded-lg p-3">
          <div className="flex items-center gap-2 text-gray-400 mb-1">
            <Clock className="w-4 h-4" />
            <span className="text-xs">Read Time</span>
          </div>
          <p className="text-xl font-bold">{document.estimated_reading_time}m</p>
        </div>
      </div>

      {/* Complexity Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Brain className="w-4 h-4" />
            <span>Complexity</span>
          </div>
          <span className="text-sm font-semibold">
            {(document.complexity_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${document.complexity_score * 100}%` }}
            transition={{ duration: 1, delay: 0.2 }}
            className={`h-full rounded-full ${
              document.complexity_score < 0.3 
                ? 'bg-green-500' 
                : document.complexity_score < 0.7 
                ? 'bg-yellow-500' 
                : 'bg-red-500'
            }`}
          />
        </div>
      </div>

      {/* Summary Toggle */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setShowDetails(!showDetails);
        }}
        className="w-full text-sm text-primary hover:text-secondary transition-colors text-left"
      >
        {showDetails ? '▼ Hide Summary' : '▶ Show Summary'}
      </button>

      {/* Expandable Summary */}
      <motion.div
        initial={false}
        animate={{ height: showDetails ? 'auto' : 0, opacity: showDetails ? 1 : 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="mt-4 pt-4 border-t border-gray-800">
          <p className="text-sm text-gray-300 mb-3 leading-relaxed">
            {document.summary}
          </p>
          
          {/* Key Topics */}
          <div className="flex flex-wrap gap-2">
            {document.key_topics.slice(0, 5).map((topic, idx) => (
              <span
                key={idx}
                className="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium"
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default DocumentCard;
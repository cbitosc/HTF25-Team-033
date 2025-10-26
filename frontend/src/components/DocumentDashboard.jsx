import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, FileText, Clock } from 'lucide-react';

const DocumentDashboard = ({ documents }) => {
  if (documents.length === 0) return null;

  const totalPages = documents.reduce((sum, doc) => sum + doc.total_pages, 0);
  const totalReadingTime = documents.reduce((sum, doc) => sum + doc.estimated_reading_time, 0);
  const avgComplexity = documents.reduce((sum, doc) => sum + doc.complexity_score, 0) / documents.length;

  const stats = [
    {
      label: 'Total Documents',
      value: documents.length,
      icon: FileText,
      color: 'from-blue-500 to-cyan-500'
    },
    {
      label: 'Total Pages',
      value: totalPages,
      icon: BarChart3,
      color: 'from-purple-500 to-pink-500'
    },
    {
      label: 'Reading Time',
      value: `${totalReadingTime}m`,
      icon: Clock,
      color: 'from-green-500 to-emerald-500'
      },
    {
      label: 'Avg Complexity',
      value: `${(avgComplexity * 100).toFixed(0)}%`,
      icon: TrendingUp,
      color: 'from-orange-500 to-red-500'
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
    >
      {stats.map((stat, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ scale: 1.05 }}
          className="glass rounded-xl p-6 relative overflow-hidden"
        >
          {/* Background Gradient */}
          <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5`} />
          
          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
            
            <div>
              <p className="text-3xl font-bold mb-1">{stat.value}</p>
              <p className="text-sm text-gray-400">{stat.label}</p>
            </div>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
};

export default DocumentDashboard;
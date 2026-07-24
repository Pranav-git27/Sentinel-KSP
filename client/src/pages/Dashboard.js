import { motion } from 'framer-motion';
import { LayoutDashboard } from 'lucide-react';
import SpatialHotspots from '../components/SpatialHotspots';
import EntityNetworkGraph from '../components/EntityNetworkGraph';
import MOSimilarityClusters from '../components/MOSimilarityClusters';

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center gap-3 mb-1">
          <LayoutDashboard className="w-5 h-5 text-accent" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Analytics Dashboard
          </h1>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400 ml-8">
          Real-time intelligence overview
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SpatialHotspots />
        <EntityNetworkGraph />
      </div>

      <MOSimilarityClusters />
    </div>
  );
}

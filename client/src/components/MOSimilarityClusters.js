import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Percent } from 'lucide-react';
import { cn } from '../lib/utils';

function ScoreBadge({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color =
    pct >= 80 ? 'bg-cyber-green/20 text-cyber-green border-cyber-green/30'
    : pct >= 50 ? 'bg-cyber-amber/20 text-cyber-amber border-cyber-amber/30'
    : 'bg-cyber-red/20 text-cyber-red border-cyber-red/30';

  return (
    <span className={cn('px-2 py-0.5 rounded-md text-xs font-mono font-bold border', color)}>
      {pct}%
    </span>
  );
}

export default function MOSimilarityClusters() {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:5000/api/analytics/mo-clusters')
      .then(r => r.json())
      .then(d => { setClusters(d); setLoading(false); })
      .catch(() => { setLoading(false); });
  }, []);

  const displayData = clusters.length ? clusters : sampleClusters;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className={cn(
        'rounded-xl border border-border dark:border-border',
        'bg-white dark:bg-card',
        'shadow-glass-light dark:shadow-glass',
        'backdrop-blur-md overflow-hidden'
      )}
    >
      <div className="flex items-center justify-between px-5 py-4 border-b border-border dark:border-border">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyber-amber/20">
            <FileText className="w-4 h-4 text-cyber-amber" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              MO Similarity Clusters
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              TF-IDF / Cosine similarity
            </p>
          </div>
        </div>
        {loading && (
          <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        )}
      </div>

      <div className="p-5 space-y-4 max-h-[400px] overflow-y-auto">
        {displayData.map((cluster, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * i }}
            className="space-y-3"
          >
            <div className="flex items-center gap-2">
              <Percent className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                Cluster {i + 1}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(cluster.cases || cluster.pairs || []).map((pair, j) => {
                const caseA = pair.case_a || pair[0];
                const caseB = pair.case_b || pair[1];
                const score = pair.similarity || pair.score || pair[2];

                return (
                  <div
                    key={j}
                    className={cn(
                      'rounded-lg border border-border dark:border-border',
                      'bg-slate-50 dark:bg-surface p-3',
                      'transition-colors'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono font-medium text-slate-900 dark:text-white">
                        {caseA}
                      </span>
                      <ScoreBadge score={score} />
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <div className="flex-1 h-px bg-border dark:bg-border" />
                      <span className="font-medium">vs</span>
                      <div className="flex-1 h-px bg-border dark:bg-border" />
                    </div>
                    <p className="mt-2 text-xs font-mono font-medium text-slate-900 dark:text-white text-right">
                      {caseB}
                    </p>
                  </div>
                );
              })}
            </div>
          </motion.div>
        ))}

        {!loading && !clusters.length && (
          <p className="text-xs text-slate-500 text-center py-4">
            No data from API — showing sample clusters. Start your backend at localhost:5000.
          </p>
        )}
      </div>
    </motion.div>
  );
}

const sampleClusters = [
  {
    pairs: [
      { case_a: 'CASE-2024-001', case_b: 'CASE-2024-042', similarity: 0.92 },
      { case_a: 'CASE-2024-001', case_b: 'CASE-2025-013', similarity: 0.78 },
    ],
  },
  {
    pairs: [
      { case_a: 'CASE-2024-089', case_b: 'CASE-2025-027', similarity: 0.85 },
      { case_a: 'CASE-2025-013', case_b: 'CASE-2025-027', similarity: 0.63 },
    ],
  },
  {
    pairs: [
      { case_a: 'CASE-2024-042', case_b: 'CASE-2024-089', similarity: 0.71 },
      { case_a: 'CASE-2024-042', case_b: 'CASE-2025-027', similarity: 0.55 },
    ],
  },
];

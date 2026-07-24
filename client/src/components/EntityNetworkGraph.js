import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Share2 } from 'lucide-react';
import { cn } from '../lib/utils';

export default function EntityNetworkGraph() {
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let network = null;

    const init = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/graph/network');
        let data;
        try { data = await res.json(); } catch (e) { data = null; }

        const { Network } = await import('vis-network/standalone');

        const nodes = (data && data.nodes && data.nodes.length)
          ? data.nodes.map(function (n) { return {
              id: n.id,
              label: n.label || n.id,
              group: n.group || 'default',
              color: nodeColor(n.group),
              font: { color: '#e2e8f0', size: 11 },
              borderWidth: 1,
              size: n.group === 'case' ? 20 : 14,
            }; })
          : getSampleNodes();

        const edges = (data && data.edges && data.edges.length)
          ? data.edges.map(function (e) { return {
              from: e.from || e.source,
              to: e.to || e.target,
              color: { color: '#475569', highlight: '#38bdf8' },
              width: 1.5,
              smooth: { type: 'curvedCW', roundness: 0.15 },
            }; })
          : getSampleEdges();

        const options = {
          physics: {
            solver: 'forceAtlas2Based',
            forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 180, springConstant: 0.02 },
            stabilization: { iterations: 100 },
          },
          nodes: { shape: 'dot', scaling: { min: 10, max: 30 } },
          edges: { arrows: { to: { enabled: true, scaleFactor: 0.5 } } },
          interaction: { hover: true, tooltipDelay: 200 },
          background: 'transparent',
        };

        if (containerRef.current) {
          network = new Network(containerRef.current, { nodes, edges }, options);
          network.on('click', p => {
            const node = nodes.find(n => n.id === p.nodes[0]);
            if (node) console.info('[Sentinel] Node clicked:', node);
          });
        }

        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    init();
    return () => { if (network) network.destroy(); };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className={cn(
        'rounded-xl border border-border dark:border-border',
        'bg-white dark:bg-card',
        'shadow-glass-light dark:shadow-glass',
        'backdrop-blur-md overflow-hidden'
      )}
    >
      <div className="flex items-center justify-between px-5 py-4 border-b border-border dark:border-border">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyber-purple/20">
            <Share2 className="w-4 h-4 text-cyber-purple" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Entity Network
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Force-directed graph
            </p>
          </div>
        </div>
        {loading && (
          <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        )}
      </div>

      <div className="relative">
        {error && (
          <div className="absolute top-3 left-3 z-10 px-3 py-1.5 rounded-lg bg-cyber-red/20 border border-cyber-red/30 text-xs text-cyber-red">
            {error}
          </div>
        )}
        <div ref={containerRef} className="h-[400px] bg-slate-950/50" />
      </div>
    </motion.div>
  );
}

function nodeColor(group) {
  if (group === 'case') return { background: '#1d4ed8', border: '#3b82f6', highlight: { background: '#2563eb', border: '#60a5fa' } };
  if (group === 'accused') return { background: '#991b1b', border: '#ef4444', highlight: { background: '#b91c1c', border: '#f87171' } };
  return { background: '#1e293b', border: '#475569', highlight: { background: '#334155', border: '#64748b' } };
}

function getSampleNodes() {
  return [
    { id: 'CASE-2024-001', label: 'CASE-2024-001', group: 'case' },
    { id: 'CASE-2024-042', label: 'CASE-2024-042', group: 'case' },
    { id: 'CASE-2024-089', label: 'CASE-2024-089', group: 'case' },
    { id: 'CASE-2025-013', label: 'CASE-2025-013', group: 'case' },
    { id: 'CASE-2025-027', label: 'CASE-2025-027', group: 'case' },
    { id: 'ACTOR-dark_helix', label: 'dark_helix', group: 'accused' },
    { id: 'ACTOR-phantom_ore', label: 'phantom_ore', group: 'accused' },
    { id: 'ACTOR-nebula_kn1ght', label: 'nebula_kn1ght', group: 'accused' },
    { id: 'ACTOR-cipher_v0id', label: 'cipher_v0id', group: 'accused' },
    { id: 'ACTOR-silent_br0ker', label: 'silent_br0ker', group: 'accused' },
    { id: 'IP-192.168.1.45', label: '192.168.1.45', group: 'ip' },
    { id: 'IP-10.0.0.23', label: '10.0.0.23', group: 'ip' },
  ];
}

function getSampleEdges() {
  return [
    { from: 'CASE-2024-001', to: 'ACTOR-dark_helix' },
    { from: 'CASE-2024-001', to: 'IP-192.168.1.45' },
    { from: 'CASE-2024-042', to: 'ACTOR-dark_helix' },
    { from: 'CASE-2024-042', to: 'ACTOR-phantom_ore' },
    { from: 'CASE-2024-089', to: 'ACTOR-phantom_ore' },
    { from: 'CASE-2024-089', to: 'ACTOR-nebula_kn1ght' },
    { from: 'CASE-2025-013', to: 'ACTOR-cipher_v0id' },
    { from: 'CASE-2025-013', to: 'ACTOR-silent_br0ker' },
    { from: 'CASE-2025-027', to: 'ACTOR-cipher_v0id' },
    { from: 'CASE-2025-027', to: 'IP-10.0.0.23' },
    { from: 'ACTOR-dark_helix', to: 'ACTOR-phantom_ore' },
    { from: 'ACTOR-cipher_v0id', to: 'ACTOR-silent_br0ker' },
  ];
}

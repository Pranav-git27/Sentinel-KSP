import { Activity, Moon, Sun, Shield } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { cn } from '../lib/utils';
import { useEffect, useState } from 'react';

function StatusBadge() {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/health', {
          signal: AbortSignal.timeout(3000),
        });
        if (mounted) setStatus(res.ok ? 'online' : 'error');
      } catch {
        if (mounted) setStatus('offline');
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const colorMap = {
    online: 'bg-cyber-green',
    offline: 'bg-cyber-red',
    error: 'bg-cyber-amber',
    checking: 'bg-slate-500',
  };

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 dark:bg-black/20 border border-white/10 backdrop-blur-sm">
      <span className={cn('w-2 h-2 rounded-full animate-pulse', colorMap[status])} />
      <span className="text-xs font-medium text-slate-300 dark:text-slate-400 capitalize">
        {status === 'checking' ? 'Connecting...' : status}
      </span>
    </div>
  );
}

export default function NavHeader() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border dark:border-border backdrop-blur-md bg-surface/70 dark:bg-surface/70">
      <div className="flex items-center justify-between h-16 px-6 max-w-[1600px] mx-auto">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-accent/20">
            <Shield className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white dark:text-white tracking-tight">
              Sentinel<span className="text-accent"> Engine</span>
            </h1>
            <p className="text-[10px] text-slate-500 dark:text-slate-500 -mt-0.5">
              Spatial & DevSecOps Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <StatusBadge />

          <div className="flex items-center gap-1">
            <Activity className="w-4 h-4 text-cyber-green" />
            <span className="text-xs text-slate-400">v0.1.0</span>
          </div>

          <button
            onClick={toggleTheme}
            className="flex items-center justify-center w-9 h-9 rounded-lg border border-border dark:border-border bg-white/5 dark:bg-black/20 hover:bg-white/10 dark:hover:bg-white/5 transition-colors"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-cyber-amber" />
            ) : (
              <Moon className="w-4 h-4 text-slate-600" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}

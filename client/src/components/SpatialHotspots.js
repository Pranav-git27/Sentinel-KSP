import { motion } from 'framer-motion';
import { MapPin, Layers } from 'lucide-react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';
import { cn } from '../lib/utils';

export default function SpatialHotspots() {
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:5000/api/spatial/hotspots')
      .then(r => r.json())
      .then(d => { setGeoData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className={cn(
        'rounded-xl border border-border dark:border-border',
        'bg-white dark:bg-card',
        'shadow-glass-light dark:shadow-glass',
        'backdrop-blur-md overflow-hidden'
      )}
    >
      <div className="flex items-center justify-between px-5 py-4 border-b border-border dark:border-border">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyber-red/20">
            <MapPin className="w-4 h-4 text-cyber-red" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Spatial Hotspots
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              DBSCAN cluster heatmap
            </p>
          </div>
        </div>
        <Layers className="w-4 h-4 text-slate-400" />
      </div>

      <div className="h-[400px] relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-black/50 z-10">
            <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        <MapContainer
          center={[20, 0]}
          zoom={2}
          className="h-full w-full"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url={document.documentElement.classList.contains('dark')
              ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
              : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
            }
          />
          {geoData && <GeoJSON data={geoData} />}
        </MapContainer>
      </div>
    </motion.div>
  );
}

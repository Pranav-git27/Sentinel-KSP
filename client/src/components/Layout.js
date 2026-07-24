import { motion } from 'framer-motion';
import NavHeader from './NavHeader';

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-surface text-slate-900 dark:text-slate-100 transition-colors">
      <NavHeader />
      <motion.main
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="p-6 max-w-[1600px] mx-auto"
      >
        {children}
      </motion.main>
    </div>
  );
}

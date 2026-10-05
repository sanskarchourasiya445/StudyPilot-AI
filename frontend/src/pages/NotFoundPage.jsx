import React from 'react';
import { Compass, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/Button';

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-[#07090d] flex items-center justify-center p-6 text-center">
      <div className="max-w-md w-full bg-[#0d1420] border border-white/[0.07] rounded-2xl p-8 shadow-2xl">
        <div className="w-16 h-16 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-6">
          <Compass className="w-8 h-8" />
        </div>
        <h1 className="text-4xl font-extrabold text-[#f5f7fa] mb-2">404</h1>
        <h2 className="text-lg font-semibold text-[#f5f7fa] mb-3">Page Not Found</h2>
        <p className="text-xs text-[#9ca8ba] mb-6">
          The study material or route you are looking for does not exist or has been moved.
        </p>
        <a href="/dashboard" className="inline-block">
          <Button variant="primary" icon={ArrowLeft}>
            Return to Dashboard
          </Button>
        </a>
      </div>
    </div>
  );
}

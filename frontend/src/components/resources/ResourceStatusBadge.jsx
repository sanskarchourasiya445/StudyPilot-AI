import React from 'react';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { Badge } from '../ui/Badge';

export function ResourceStatusBadge({ status = 'ready' }) {
  const statusLower = (status || 'ready').toLowerCase();

  if (statusLower === 'ready') {
    return (
      <Badge variant="success">
        <CheckCircle2 className="w-3 h-3 text-green-600 dark:text-green-400" />
        <span>Ready</span>
      </Badge>
    );
  }

  if (statusLower === 'processing') {
    return (
      <Badge variant="warning">
        <Loader2 className="w-3 h-3 animate-spin text-amber-600 dark:text-amber-400" />
        <span>Processing</span>
      </Badge>
    );
  }

  return (
    <Badge variant="danger">
      <AlertCircle className="w-3 h-3 text-red-600 dark:text-red-400" />
      <span>Failed</span>
    </Badge>
  );
}

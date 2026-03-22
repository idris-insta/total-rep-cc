/**
 * Loading Spinner Component
 */
import React from 'react';

const LoadingSpinner = ({ size = 'md', message }) => {
  const sizeClasses = {
    sm: 'h-6 w-6 border-2',
    md: 'h-12 w-12 border-4',
    lg: 'h-16 w-16 border-4'
  };

  return (
    <div className="flex flex-col items-center justify-center h-96">
      <div className={`animate-spin ${sizeClasses[size]} border-accent border-t-transparent rounded-full`}></div>
      {message && <p className="mt-4 text-slate-500">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;

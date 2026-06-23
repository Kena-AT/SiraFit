import { Suspense } from 'react';
import ResetPasswordContent from './ResetPasswordContent';

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex flex-col items-center justify-center p-4 min-h-screen">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"/>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}

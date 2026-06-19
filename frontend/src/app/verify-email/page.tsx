import { Suspense } from 'react';
import VerifyEmailContent from './VerifyEmailContent';

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"/>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}

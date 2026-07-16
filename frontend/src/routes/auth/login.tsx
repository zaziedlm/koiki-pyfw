import { LoginForm } from '@/components/auth/login-form';
import { PublicRoute } from '@/components/auth/auth-guard';
import { config } from '@/lib/config';

export default function LoginPage() {
  return (
    <PublicRoute>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {config.app.name}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Task Management System
            </p>
          </div>
          
          <LoginForm />
        </div>
      </div>
    </PublicRoute>
  );
}
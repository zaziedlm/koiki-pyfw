'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useLogin } from '@/hooks';
import { useCookieLogin } from '@/hooks/use-cookie-auth-queries';
import { useUIStore } from '@/stores';
import { Loader2, Eye, EyeOff } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();
  const addNotification = useUIStore((state) => state.addNotification);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // 認証方式の設定（環境変数で制御）
  const useLocalStorageAuth = process.env.NEXT_PUBLIC_USE_LOCALSTORAGE_AUTH === 'true';
  
  console.log('🔐 LoginForm - Auth method:', { useLocalStorageAuth });
  
  // Hooksは必ず呼び出す（条件付き呼び出しは禁止）
  const localStorageLoginMutation = useLogin();
  const cookieLoginMutation = useCookieLogin();
  
  // 使用するmutationを選択
  const loginMutation = useLocalStorageAuth ? localStorageLoginMutation : cookieLoginMutation;

  const onSubmit = async (data: LoginFormData) => {
    console.log('=== Login Form Submit ===');
    console.log('Login data:', data);
    console.log('Using localStorage auth:', useLocalStorageAuth);
    
    try {
      console.log('Calling loginMutation.mutateAsync...');
      const result = await loginMutation.mutateAsync(data);
      console.log('Login mutation result:', result);
      console.log('Login mutation completed successfully');
      
      addNotification({
        type: 'success',
        title: 'ログイン成功',
        message: 'おかえりなさい！',
      });
      
      // Cookie認証の場合はmutation のonSuccessでリダイレクト処理が実行される
      if (!useLocalStorageAuth) {
        console.log('Cookie auth: Waiting for mutation onSuccess to handle redirect...');
        // useCookieLogin の onSuccess でリダイレクト処理が実行される
      } else {
        console.log('LocalStorage auth: using router.push...');
        router.push('/dashboard');
      }
      
    } catch (error: unknown) {
      console.error('Login error in form:', error);
      let errorMessage = 'メールアドレスまたはパスワードが正しくありません';
      
      if (error instanceof Error) {
        errorMessage = error.message;
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
      } else if (useLocalStorageAuth) {
        // localStorage認証のエラーハンドリング
        errorMessage = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || errorMessage;
      }
      
      addNotification({
        type: 'error',
        title: 'ログイン失敗',
        message: errorMessage,
      });
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">Sign In</CardTitle>
        <CardDescription className="text-center">
          Enter your email and password to access your account
        </CardDescription>
      </CardHeader>
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              {...register('email')}
              className={errors.email ? 'border-red-500' : ''}
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email.message}</p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                {...register('password')}
                className={errors.password ? 'border-red-500 pr-10' : 'pr-10'}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && (
              <p className="text-sm text-red-500">{errors.password.message}</p>
            )}
          </div>
        </CardContent>
        
        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
          
          <div className="text-center text-sm text-gray-600">
            Don&apos;t have an account?{' '}
            <Link
              href="/auth/register"
              className="text-primary hover:underline font-medium"
            >
              Sign up
            </Link>
          </div>
          
          <div className="text-center">
            <Link
              href="/auth/forgot-password"
              className="text-sm text-primary hover:underline"
            >
              Forgot your password?
            </Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useCookieAuth } from '@/hooks/use-cookie-auth-queries';
import { config } from '@/lib/config';
import { CheckCircle, Users, Shield, Clock } from 'lucide-react';

export default function Home() {
  const router = useRouter();

  const { isAuthenticated, isLoading } = useCookieAuth();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const features = [
    {
      icon: CheckCircle,
      title: 'Task Management',
      description: 'Create, organize, and track your tasks efficiently',
    },
    {
      icon: Users,
      title: 'User Management',
      description: 'Role-based access control and user administration',
    },
    {
      icon: Shield,
      title: 'Security',
      description: 'Enterprise-grade security with comprehensive monitoring',
    },
    {
      icon: Clock,
      title: 'Real-time Updates',
      description: 'Stay synchronized with real-time task updates',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="border-b bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {config.app.name}
          </h1>
          <div className="space-x-4">
            <Button variant="ghost" asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/auth/register">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="max-w-3xl mx-auto space-y-8">
          <h2 className="text-5xl font-bold text-gray-900 dark:text-white leading-tight">
            Manage Your Tasks
            <span className="text-primary block">Like a Pro</span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 leading-relaxed">
            A modern, secure task management system built with cutting-edge technology.
            Organize your work, collaborate with your team, and achieve your goals.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/auth/register">Start Free Trial</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/auth/login">Sign In</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Powerful Features
          </h3>
          <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Everything you need to manage tasks effectively and securely
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="text-center border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="mx-auto mb-4 w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary/5 dark:bg-primary/10">
        <div className="container mx-auto px-4 py-16 text-center">
          <div className="max-w-2xl mx-auto space-y-6">
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white">
              Ready to Get Started?
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Join thousands of users who are already managing their tasks more effectively.
            </p>
            <Button size="lg" asChild>
              <Link href="/auth/register">Create Your Account</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8 text-center text-gray-600 dark:text-gray-300">
          <p>&copy; 2024 {config.app.name}. Built with Next.js 15 and FastAPI.</p>
        </div>
      </footer>
    </div>
  );
}

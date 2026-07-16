import { Link } from 'react-router';
import { formatDistanceToNow } from 'date-fns';
import { CheckSquare, Circle, ListTodo, TrendingUp } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useCookieTodos } from '@/features/tasks/queries';
import type { TodoResponse } from '@/types';

function byUpdatedAtDesc(a: TodoResponse, b: TodoResponse) {
  return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
}

export default function DashboardPage() {
  const { data: todos = [], isLoading, error } = useCookieTodos();

  const total = todos.length;
  const completed = todos.filter((todo) => todo.is_completed).length;
  const pending = total - completed;
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
  const recentTasks = [...todos].sort(byUpdatedAtDesc).slice(0, 5);

  const stats = [
    {
      name: 'Total Tasks',
      value: total,
      description: 'Tasks available to your account',
      icon: ListTodo,
    },
    {
      name: 'Completed',
      value: completed,
      description: 'Tasks marked as complete',
      icon: TrendingUp,
    },
    {
      name: 'Pending',
      value: pending,
      description: 'Tasks still in progress',
      icon: Circle,
    },
    {
      name: 'Completion Rate',
      value: `${completionRate}%`,
      description: 'Completed tasks divided by total tasks',
      icon: CheckSquare,
    },
  ];

  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-6 text-center text-red-500">
            Failed to load dashboard data. Please refresh the page.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Current task status from the backend task API.
          </p>
        </div>
        <Button asChild>
          <Link to="/dashboard/tasks">Open Tasks</Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.name}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? '-' : stat.value}
              </div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-7">
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Recently Updated Tasks</CardTitle>
            <CardDescription>
              Latest task activity from your task list
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, index) => (
                  <div key={index} className="animate-pulse space-y-2">
                    <div className="h-4 w-3/4 rounded bg-muted" />
                    <div className="h-3 w-1/2 rounded bg-muted" />
                  </div>
                ))}
              </div>
            ) : recentTasks.length === 0 ? (
              <div className="rounded-md border border-dashed p-6 text-center">
                <p className="text-sm font-medium">No tasks yet</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Create your first task to populate this dashboard.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentTasks.map((task) => (
                  <div key={task.id} className="flex items-center gap-4">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        task.is_completed ? 'bg-green-500' : 'bg-orange-500'
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {task.title}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Updated {formatDistanceToNow(new Date(task.updated_at), { addSuffix: true })}
                      </p>
                    </div>
                    <Badge variant={task.is_completed ? 'default' : 'secondary'}>
                      {task.is_completed ? 'Completed' : 'Pending'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Task Actions</CardTitle>
            <CardDescription>
              Common task and workspace shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button asChild className="w-full justify-start" variant="outline">
                <Link to="/dashboard/tasks">Create new task</Link>
              </Button>
              <Button asChild className="w-full justify-start" variant="outline">
                <Link to="/dashboard/tasks">View all tasks</Link>
              </Button>
              <Button asChild className="w-full justify-start" variant="outline">
                <Link to="/dashboard/users">Team overview</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

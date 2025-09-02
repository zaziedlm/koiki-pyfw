import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ProtectedRoute } from '@/components/auth/auth-guard';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckSquare, Users, Clock, TrendingUp } from 'lucide-react';

export default function DashboardPage() {
  const stats = [
    {
      name: 'Total Tasks',
      value: '12',
      description: 'Active tasks in your workspace',
      icon: CheckSquare,
      trend: '+2 from yesterday',
    },
    {
      name: 'Completed',
      value: '8',
      description: 'Tasks completed this week',
      icon: TrendingUp,
      trend: '+12% from last week',
    },
    {
      name: 'In Progress',
      value: '4',
      description: 'Currently active tasks',
      icon: Clock,
      trend: 'No change',
    },
    {
      name: 'Team Members',
      value: '6',
      description: 'Active team members',
      icon: Users,
      trend: '+1 new member',
    },
  ];

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="p-6 space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Here&apos;s an overview of your tasks and activities.
            </p>
          </div>

          {/* Stats Grid */}
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
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">
                    {stat.description}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    {stat.trend}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Recent Activity */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Recent Tasks</CardTitle>
                <CardDescription>
                  Your most recently updated tasks
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { title: 'Review API documentation', status: 'completed', time: '2 hours ago' },
                    { title: 'Update user interface', status: 'in-progress', time: '4 hours ago' },
                    { title: 'Fix login bug', status: 'completed', time: '1 day ago' },
                    { title: 'Design new dashboard', status: 'pending', time: '2 days ago' },
                  ].map((task, index) => (
                    <div key={index} className="flex items-center space-x-4">
                      <div className={`w-2 h-2 rounded-full ${
                        task.status === 'completed' ? 'bg-green-500' :
                        task.status === 'in-progress' ? 'bg-blue-500' : 'bg-gray-400'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {task.title}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {task.time}
                        </p>
                      </div>
                      <div className={`text-xs px-2 py-1 rounded-full ${
                        task.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                        task.status === 'in-progress' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' : 
                        'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                      }`}>
                        {task.status.replace('-', ' ')}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common tasks and shortcuts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <button className="w-full text-left p-3 rounded-lg border hover:bg-accent transition-colors">
                    <div className="font-medium">Create New Task</div>
                    <div className="text-sm text-muted-foreground">
                      Add a new task to your workspace
                    </div>
                  </button>
                  <button className="w-full text-left p-3 rounded-lg border hover:bg-accent transition-colors">
                    <div className="font-medium">View All Tasks</div>
                    <div className="text-sm text-muted-foreground">
                      See all your tasks in one place
                    </div>
                  </button>
                  <button className="w-full text-left p-3 rounded-lg border hover:bg-accent transition-colors">
                    <div className="font-medium">Team Overview</div>
                    <div className="text-sm text-muted-foreground">
                      Check team progress and activity
                    </div>
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
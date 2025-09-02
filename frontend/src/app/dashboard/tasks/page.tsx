'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ProtectedRoute } from '@/components/auth/auth-guard';
import { TaskList } from '@/components/tasks/task-list';
import { TodoFilter } from '@/types';

export default function TasksPage() {
  const [filter, setFilter] = useState<TodoFilter>({});

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="p-6">
          <TaskList filter={filter} onFilterChange={setFilter} />
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
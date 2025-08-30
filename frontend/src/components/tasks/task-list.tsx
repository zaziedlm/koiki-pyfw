'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Search, 
  Plus, 
  MoreVertical, 
  Edit, 
  Trash2, 
  Calendar,
  Filter,
  CheckCircle2,
  Circle,
  Clock
} from 'lucide-react';
import { useTodos, useUpdateTodo } from '@/hooks';
import { TodoResponse, TodoFilter } from '@/types';
import { useUIStore } from '@/stores';
import { formatDistanceToNow } from 'date-fns';
import { TaskCreateDialog } from './task-create-dialog';
import { TaskEditDialog } from './task-edit-dialog';
import { TaskDeleteDialog } from './task-delete-dialog';

interface TaskListProps {
  filter?: TodoFilter;
  onFilterChange?: (filter: TodoFilter) => void;
}

export function TaskList({ filter = {}, onFilterChange }: TaskListProps) {
  const [searchTerm, setSearchTerm] = useState(filter.search || '');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<TodoResponse | null>(null);
  const [deletingTask, setDeletingTask] = useState<TodoResponse | null>(null);
  
  const { data: todos, isLoading, error } = useTodos();
  const updateTaskMutation = useUpdateTodo();
  const addNotification = useUIStore((state) => state.addNotification);

  // Filter todos based on current filter
  const filteredTodos = todos?.filter((todo: TodoResponse) => {
    const matchesSearch = !searchTerm || 
      todo.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      todo.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filter.completed === undefined || 
      todo.is_completed === filter.completed;
    
    return matchesSearch && matchesStatus;
  }) || [];

  const handleToggleComplete = async (todo: TodoResponse) => {
    try {
      await updateTaskMutation.mutateAsync({
        id: todo.id,
        data: { is_completed: !todo.is_completed }
      });
      
      addNotification({
        type: 'success',
        title: todo.is_completed ? 'Task marked as incomplete' : 'Task completed',
        message: `"${todo.title}" has been updated`,
      });
    } catch {
      addNotification({
        type: 'error',
        title: 'Failed to update task',
        message: 'Please try again',
      });
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    onFilterChange?.({ ...filter, search: value });
  };

  const handleFilterChange = (newFilter: Partial<TodoFilter>) => {
    const updatedFilter = { ...filter, ...newFilter };
    onFilterChange?.(updatedFilter);
  };

  const getTaskStats = () => {
    const total = filteredTodos.length;
    const completed = filteredTodos.filter((t: TodoResponse) => t.is_completed).length;
    const pending = total - completed;
    return { total, completed, pending };
  };

  const stats = getTaskStats();

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-500">
            <p>Failed to load tasks. Please try refreshing the page.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Tasks</h2>
          <p className="text-muted-foreground">
            Manage and track your tasks
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Task
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Circle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.pending}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tasks..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <Filter className="mr-2 h-4 w-4" />
              Filter
              {filter.completed !== undefined && (
                <Badge variant="secondary" className="ml-2">
                  {filter.completed ? 'Completed' : 'Pending'}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleFilterChange({ completed: undefined })}>
              All Tasks
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleFilterChange({ completed: false })}>
              Pending Only
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleFilterChange({ completed: true })}>
              Completed Only
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Task List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <div className="animate-pulse space-y-2">
                    <div className="h-4 bg-muted rounded w-3/4"></div>
                    <div className="h-3 bg-muted rounded w-1/2"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : filteredTodos.length === 0 ? (
          <Card>
            <CardContent className="p-8">
              <div className="text-center space-y-4">
                <CheckCircle2 className="h-12 w-12 text-muted-foreground mx-auto" />
                <div>
                  <h3 className="text-lg font-medium">No tasks found</h3>
                  <p className="text-muted-foreground">
                    {searchTerm || filter.completed !== undefined
                      ? "Try adjusting your search or filter"
                      : "Get started by creating your first task"
                    }
                  </p>
                </div>
                {!searchTerm && filter.completed === undefined && (
                  <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create First Task
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredTodos.map((todo: TodoResponse) => (
            <Card key={todo.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <Checkbox
                    checked={todo.is_completed}
                    onCheckedChange={() => handleToggleComplete(todo)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 
                          className={`font-medium ${
                            todo.is_completed 
                              ? 'text-muted-foreground line-through' 
                              : 'text-foreground'
                          }`}
                        >
                          {todo.title}
                        </h3>
                        {todo.description && (
                          <p 
                            className={`text-sm mt-1 ${
                              todo.is_completed 
                                ? 'text-muted-foreground line-through' 
                                : 'text-muted-foreground'
                            }`}
                          >
                            {todo.description}
                          </p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-xs text-muted-foreground">
                          <div className="flex items-center">
                            <Calendar className="mr-1 h-3 w-3" />
                            Created {formatDistanceToNow(new Date(todo.created_at), { addSuffix: true })}
                          </div>
                          {todo.updated_at !== todo.created_at && (
                            <div className="flex items-center">
                              <Clock className="mr-1 h-3 w-3" />
                              Updated {formatDistanceToNow(new Date(todo.updated_at), { addSuffix: true })}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <Badge variant={todo.is_completed ? "default" : "secondary"}>
                          {todo.is_completed ? "Completed" : "Pending"}
                        </Badge>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <MoreVertical className="h-4 w-4" />
                              <span className="sr-only">Open menu</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => setEditingTask(todo)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => setDeletingTask(todo)}
                              className="text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Dialogs */}
      <TaskCreateDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
      
      {editingTask && (
        <TaskEditDialog
          task={editingTask}
          open={!!editingTask}
          onOpenChange={(open) => !open && setEditingTask(null)}
        />
      )}
      
      {deletingTask && (
        <TaskDeleteDialog
          task={deletingTask}
          open={!!deletingTask}
          onOpenChange={(open) => !open && setDeletingTask(null)}
        />
      )}
    </div>
  );
}
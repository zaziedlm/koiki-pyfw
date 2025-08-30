'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { useUpdateTodo } from '@/hooks';
import { useCookieUpdateTodo } from '@/hooks/use-cookie-todo-queries';
import { useUIStore } from '@/stores';
import { TodoResponse } from '@/types';
import { Loader2 } from 'lucide-react';

const editTaskSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(255, 'Title must be less than 255 characters'),
  description: z
    .string()
    .optional()
    .or(z.literal('')),
  is_completed: z.boolean(),
});

type EditTaskFormData = z.infer<typeof editTaskSchema>;

interface TaskEditDialogProps {
  task: TodoResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TaskEditDialog({ task, open, onOpenChange }: TaskEditDialogProps) {
  const addNotification = useUIStore((state) => state.addNotification);
  // 認証方式に応じてhooksを選択
  const useLocalStorageAuth = process.env.NEXT_PUBLIC_USE_LOCALSTORAGE_AUTH === 'true';
  const localUpdateMutation = useUpdateTodo();
  const cookieUpdateMutation = useCookieUpdateTodo();
  const updateTaskMutation = useLocalStorageAuth ? localUpdateMutation : cookieUpdateMutation;

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<EditTaskFormData>({
    resolver: zodResolver(editTaskSchema),
    defaultValues: {
      title: task.title,
      description: task.description || '',
      is_completed: task.is_completed,
    },
  });

  const isCompleted = watch('is_completed');

  // Reset form when task changes
  useEffect(() => {
    reset({
      title: task.title,
      description: task.description || '',
      is_completed: task.is_completed,
    });
  }, [task, reset]);

  const onSubmit = async (data: EditTaskFormData) => {
    try {
      await updateTaskMutation.mutateAsync({
        id: task.id,
        data: {
          title: data.title,
          description: data.description || undefined,
          is_completed: data.is_completed,
        },
      });

      addNotification({
        type: 'success',
        title: 'Task updated',
        message: `"${data.title}" has been updated`,
      });

      onOpenChange(false);
    } catch (error: unknown) {
      const message = error instanceof Error && 'response' in error 
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Please try again'
        : 'Please try again';
      
      addNotification({
        type: 'error',
        title: 'Failed to update task',
        message,
      });
    }
  };

  const handleClose = () => {
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Task</DialogTitle>
          <DialogDescription>
            Make changes to your task
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Enter task title"
              {...register('title')}
              className={errors.title ? 'border-red-500' : ''}
            />
            {errors.title && (
              <p className="text-sm text-red-500">{errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              placeholder="Enter task description"
              rows={3}
              {...register('description')}
              className={errors.description ? 'border-red-500' : ''}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_completed"
              checked={isCompleted}
              onCheckedChange={(checked) => setValue('is_completed', !!checked, { shouldDirty: true })}
            />
            <Label htmlFor="is_completed" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Mark as completed
            </Label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={updateTaskMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateTaskMutation.isPending || !isDirty}
            >
              {updateTaskMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Task'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
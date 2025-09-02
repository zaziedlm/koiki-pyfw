'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useCookieDeleteTodo } from '@/hooks/use-cookie-todo-queries';
import { useUIStore } from '@/stores';
import { TodoResponse } from '@/types';
import { Loader2, AlertTriangle } from 'lucide-react';

interface TaskDeleteDialogProps {
  task: TodoResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TaskDeleteDialog({ task, open, onOpenChange }: TaskDeleteDialogProps) {
  const addNotification = useUIStore((state) => state.addNotification);

  const deleteTaskMutation = useCookieDeleteTodo();

  const handleDelete = async () => {
    try {
      await deleteTaskMutation.mutateAsync(task.id);

      addNotification({
        type: 'success',
        title: 'Task deleted',
        message: `"${task.title}" has been removed`,
      });

      onOpenChange(false);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Please try again';
      addNotification({
        type: 'error',
        title: 'Failed to delete task',
        message,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <span>Delete Task</span>
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this task? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-medium">{task.title}</h4>
            {task.description && (
              <p className="text-sm text-muted-foreground mt-1">
                {task.description}
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={deleteTaskMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteTaskMutation.isPending}
          >
            {deleteTaskMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete Task'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

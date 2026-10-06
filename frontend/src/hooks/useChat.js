import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../services/chatApi';
import { useToast } from '../components/ui/Toast';

export function useSendMessage() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (variables) => chatApi.sendMessage(variables),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      if (data.conversation_id) {
        queryClient.invalidateQueries({ queryKey: ['messages', data.conversation_id] });
      }
    },
    onError: (error) => {
      addToast(error.message || 'Failed to send message to AI assistant.', 'error');
    },
  });
}

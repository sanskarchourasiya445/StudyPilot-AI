import { useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../services/chatApi';
import { useToast } from '../components/ui/Toast';

export function useSendMessage() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ message, resource_id, conversation_id }) =>
      chatApi.sendMessage({ message, resource_id, conversation_id }),
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

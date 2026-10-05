import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationApi } from '../services/conversationApi';
import { useToast } from '../components/ui/Toast';

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: conversationApi.getConversations,
  });
}

export function useConversationMessages(conversationId) {
  const isValid = Boolean(conversationId) && conversationId !== 'undefined' && conversationId !== 'null';
  return useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => conversationApi.getMessages(conversationId),
    enabled: isValid,
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (conversationId) => conversationApi.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      addToast('Conversation deleted.', 'info');
    },
    onError: (error) => {
      addToast(error.message || 'Failed to delete conversation.', 'error');
    },
  });
}

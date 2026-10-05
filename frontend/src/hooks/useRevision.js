import { useQuery } from '@tanstack/react-query';
import { revisionApi } from '../services/revisionApi';

export function useRevisionSchedule() {
  return useQuery({
    queryKey: ['revision_schedule'],
    queryFn: revisionApi.getSchedule,
    staleTime: 1000 * 60 * 2,
  });
}

export function useDueRevisions() {
  return useQuery({
    queryKey: ['revision_due'],
    queryFn: revisionApi.getDue,
    staleTime: 1000 * 60 * 2,
  });
}

export function useUpcomingRevisions(limit = 10) {
  return useQuery({
    queryKey: ['revision_upcoming', limit],
    queryFn: () => revisionApi.getUpcoming(limit),
    staleTime: 1000 * 60 * 2,
  });
}

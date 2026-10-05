import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Video, Trash2, ExternalLink } from 'lucide-react';
import { ResourceStatusBadge } from './ResourceStatusBadge';

export function ResourceTable({ resources, onDelete }) {
  const navigate = useNavigate();

  return (
    <div className="w-full overflow-x-auto border border-white/[0.07] rounded-2xl bg-[#0d1420] shadow-sm">
      <table className="w-full text-left border-collapse text-xs md:text-sm">
        <thead>
          <tr className="bg-[#0a0f18] border-b border-white/[0.07] text-[#9ca8ba] font-semibold">
            <th className="py-3 px-4">Title / Source</th>
            <th className="py-3 px-4">Type</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4">Date Added</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.05] text-[#f5f7fa]">
          {resources.map((resource) => {
            const isPdf = resource.source_type === 'pdf';
            return (
              <tr
                key={resource.id}
                onClick={() => navigate(`/resources/${resource.resource_id}`)}
                className="hover:bg-white/[0.03] cursor-pointer transition-colors"
              >
                <td className="py-3.5 px-4 font-medium max-w-xs truncate">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                        isPdf
                          ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400'
                          : 'bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400'
                      }`}
                    >
                      {isPdf ? <FileText className="w-4 h-4" /> : <Video className="w-4 h-4" />}
                    </div>
                    <span className="truncate">{resource.title || resource.source}</span>
                  </div>
                </td>
                <td className="py-3.5 px-4 uppercase text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                  {resource.source_type}
                </td>
                <td className="py-3.5 px-4">
                  <ResourceStatusBadge status={resource.status} />
                </td>
                <td className="py-3.5 px-4 text-slate-500 dark:text-slate-400 text-xs">
                  {new Date(resource.created_at).toLocaleDateString()}
                </td>
                <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => navigate(`/resources/${resource.resource_id}`)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                      title="View Details"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    {onDelete && (
                      <button
                        onClick={() => onDelete(resource)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        title="Delete Resource"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

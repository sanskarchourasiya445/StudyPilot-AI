import React, { useState, useRef } from 'react';
import { FileText, Video, UploadCloud, X, Link as LinkIcon, AlertCircle } from 'lucide-react';
import { useUploadPdf, useAddYoutube } from '../../hooks/useResources';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

export function ResourceUploadModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('pdf'); // 'pdf' | 'youtube'
  const [selectedFile, setSelectedFile] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);

  const fileInputRef = useRef(null);
  const uploadPdfMutation = useUploadPdf();
  const addYoutubeMutation = useAddYoutube();

  if (!isOpen) return null;

  const isSubmitting = uploadPdfMutation.isPending || addYoutubeMutation.isPending;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return false;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setValidationError('Only .pdf files are supported.');
      return false;
    }
    if (file.size > 50 * 1024 * 1024) {
      setValidationError('File size exceeds 50MB limit.');
      return false;
    }
    setValidationError(null);
    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handlePdfSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setValidationError('Please select a PDF file.');
      return;
    }
    setValidationError(null);
    try {
      await uploadPdfMutation.mutateAsync(selectedFile);
      setSelectedFile(null);
      onClose();
    } catch {
      // Handled by mutation toast & error state
    }
  };

  const handleYoutubeSubmit = async (e) => {
    e.preventDefault();
    const trimmed = youtubeUrl.trim();
    if (!trimmed) {
      setValidationError('Please enter a YouTube video URL.');
      return;
    }
    if (!trimmed.includes('youtube.com') && !trimmed.includes('youtu.be')) {
      setValidationError('Invalid YouTube URL format. Expected youtube.com or youtu.be link.');
      return;
    }
    setValidationError(null);
    try {
      await addYoutubeMutation.mutateAsync(trimmed);
      setYoutubeUrl('');
      onClose();
    } catch {
      // Handled by mutation toast
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#050505]/80 backdrop-blur-md animate-in fade-in duration-150">
      <div className="bg-[#0d1420] border border-white/[0.08] rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          disabled={isSubmitting}
          className="absolute top-4 right-4 text-[#9ca8ba] hover:text-[#f5f7fa] p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-lg font-bold text-[#f5f7fa] mb-1">
          Add Study Material
        </h2>
        <p className="text-xs text-[#9ca8ba] mb-5">
          Ingest textbooks or lecture videos into your unified RAG knowledge base.
        </p>

        {/* Tab switcher: PDF vs YouTube */}
        <div className="flex items-center gap-1.5 p-1 bg-[#0a0f18] rounded-xl border border-white/[0.06] mb-5">
          <button
            type="button"
            onClick={() => {
              setActiveTab('pdf');
              setValidationError(null);
            }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'pdf'
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                : 'text-[#9ca8ba] hover:text-[#f5f7fa] hover:bg-white/[0.04]'
            }`}
          >
            <FileText className="w-4 h-4" />
            PDF Document
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('youtube');
              setValidationError(null);
            }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'youtube'
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                : 'text-[#9ca8ba] hover:text-[#f5f7fa] hover:bg-white/[0.04]'
            }`}
          >
            <Video className="w-4 h-4" />
            YouTube Lecture
          </button>
        </div>

        {validationError && (
          <div className="mb-4 p-3 rounded-xl bg-red-950/40 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{validationError}</span>
          </div>
        )}

        {activeTab === 'pdf' ? (
          <form onSubmit={handlePdfSubmit}>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                dragActive
                  ? 'border-blue-500 bg-blue-600/10'
                  : 'border-white/[0.12] bg-[#0a0f18]/60 hover:border-blue-500/50 hover:bg-[#0a0f18]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleFileChange}
              />
              <UploadCloud className="w-10 h-10 text-blue-400 mx-auto mb-2" />
              {selectedFile ? (
                <div>
                  <p className="text-sm font-semibold text-[#f5f7fa]">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-[#9ca8ba] mt-1">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready to ingest
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-semibold text-[#f5f7fa]">
                    Click to select a PDF or drag & drop file here
                  </p>
                  <p className="text-xs text-[#667085] mt-1">
                    Textbooks, papers, lecture notes up to 50MB
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="secondary" size="sm" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={uploadPdfMutation.isPending}
                disabled={!selectedFile}
              >
                Upload & Ingest PDF
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleYoutubeSubmit}>
            <div className="space-y-4">
              <div>
                <Input
                  label="YouTube Lecture URL"
                  icon={LinkIcon}
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  disabled={isSubmitting}
                  autoFocus
                />
              </div>

              <div className="p-3.5 rounded-xl bg-[#0a0f18] border border-white/[0.06] text-xs text-[#9ca8ba] space-y-1.5">
                <div className="flex items-center gap-1.5 text-blue-400 font-semibold">
                  <Video className="w-3.5 h-3.5" />
                  <span>Automated Transcript Pipeline</span>
                </div>
                <p className="text-[#667085] leading-relaxed">
                  StudyPilot extracts video captions or falls back to audio transcription. Video segments are chunked and indexed into ChromaDB alongside your PDF notes.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <Button variant="secondary" size="sm" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={addYoutubeMutation.isPending}
                disabled={!youtubeUrl.trim()}
              >
                Ingest YouTube Video
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

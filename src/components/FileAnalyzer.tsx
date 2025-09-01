import React, { useState, useRef } from 'react';
import { Upload, CheckCircle, Loader2, RotateCcw } from 'lucide-react';

interface FileAnalysisResult {
  fileName: string;
  fileSize: string;
  fileType: string;
  lastModified: string;
  checksum: string;
  encoding: string;
}

type AnalyzerState = 'idle' | 'dragover' | 'processing' | 'complete';

const FileAnalyzer: React.FC = () => {
  const [state, setState] = useState<AnalyzerState>('idle');
  const [analysisResult, setAnalysisResult] = useState<FileAnalysisResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  const handleFileSelect = (file: File) => {
    setState('processing');
    
    // Simulate file analysis
    setTimeout(() => {
      const result: FileAnalysisResult = {
        fileName: file.name,
        fileSize: formatFileSize(file.size),
        fileType: file.type || 'Unknown',
        lastModified: new Date(file.lastModified).toLocaleDateString(),
        checksum: generateMockChecksum(),
        encoding: detectMockEncoding(file.name),
      };
      
      setAnalysisResult(result);
      setState('complete');
    }, 2000);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current++;
    if (dragCounterRef.current === 1) {
      setState('dragover');
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setState('idle');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounterRef.current = 0;
    setState('idle');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    if (state === 'idle' || state === 'dragover') {
      fileInputRef.current?.click();
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleReset = () => {
    setState('idle');
    setAnalysisResult(null);
    dragCounterRef.current = 0;
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const generateMockChecksum = (): string => {
    return 'sha256:' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  };

  const detectMockEncoding = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'txt': case 'csv': case 'json': case 'xml': case 'html': case 'css': case 'js':
        return 'UTF-8';
      case 'pdf':
        return 'Binary (PDF)';
      case 'jpg': case 'jpeg': case 'png': case 'gif': case 'bmp':
        return 'Binary (Image)';
      default:
        return 'Auto-detected';
    }
  };

  if (state === 'complete' && analysisResult) {
    return (
      <div className="analysis-card">
        <div className="analysis-header">
          <CheckCircle className="w-6 h-6 text-success-500" />
          <h4>Analysis Complete</h4>
        </div>
        
        <div className="analysis-divider"></div>
        
        <div className="space-y-2">
          <div className="analysis-row">
            <span className="analysis-key">File Name:</span>
            <span className="analysis-value">{analysisResult.fileName}</span>
          </div>
          
          <div className="analysis-row">
            <span className="analysis-key">File Size:</span>
            <span className="analysis-value">{analysisResult.fileSize}</span>
          </div>
          
          <div className="analysis-row">
            <span className="analysis-key">File Type:</span>
            <span className="analysis-value">{analysisResult.fileType}</span>
          </div>
          
          <div className="analysis-row">
            <span className="analysis-key">Last Modified:</span>
            <span className="analysis-value">{analysisResult.lastModified}</span>
          </div>
          
          <div className="analysis-row">
            <span className="analysis-key">Checksum:</span>
            <span className="analysis-value font-mono text-sm">{analysisResult.checksum}</span>
          </div>
          
          <div className="analysis-row">
            <span className="analysis-key">Encoding:</span>
            <span className="analysis-value">{analysisResult.encoding}</span>
          </div>
        </div>
        
        <div className="analysis-divider"></div>
        
        <button 
          onClick={handleReset}
          className="flex items-center gap-2 text-primary-500 hover:text-blue-600 transition-colors duration-200 text-sm font-medium"
        >
          <RotateCcw className="w-4 h-4" />
          Analyze another file
        </button>
      </div>
    );
  }

  if (state === 'processing') {
    return (
      <div className="drop-zone">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="loading-spinner" />
          <p className="label text-gray-700">Analyzing file...</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`drop-zone ${state === 'dragover' ? 'drag-over' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileInputChange}
        className="hidden"
        accept="*/*"
      />
      
      <div className="flex flex-col items-center gap-4">
        <Upload className="drop-zone-icon" />
        <div className="text-center">
          <p className="drop-zone-text">Drag & drop a file here, or click to select</p>
          <p className="caption mt-2">Max file size: 50MB</p>
        </div>
      </div>
    </div>
  );
};

export default FileAnalyzer;
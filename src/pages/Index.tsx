import FileAnalyzer from '@/components/FileAnalyzer';

const Index = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="content-container">
        <header className="text-center mb-10">
          <h1 className="mb-4">Backbooking Analyzer</h1>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto">
            <strong>Instructions:</strong> Drag & Drop Backbooking "Missing Backbooking Records by Day" File
          </p>
        </header>
        
        <main className="max-w-2xl mx-auto">
          <FileAnalyzer />
        </main>
        
        <footer className="mt-16 pt-8 border-t border-gray-200 text-center">
        </footer>
      </div>
    </div>
  );
};

export default Index;
import FileAnalyzer from '@/components/FileAnalyzer';

const Index = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="content-container">
        <header className="text-center mb-10">
          <h1 className="mb-4">Backbooking Analyzer</h1>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto">
            Instructions: Drag and drop backbooking Missing Backbooking Records by Day file
          </p>
        </header>
        
        <main className="max-w-2xl mx-auto">
          <FileAnalyzer />
        </main>
        
        <footer className="mt-16 pt-8 border-t border-gray-200 text-center">
          <p className="caption">
            Built with precision engineering for data professionals and analysts
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Index;
import { useState, useEffect } from 'react';
import { useResearchList } from './hooks/useResearch';
import ResearchForm from './components/ResearchForm';
import ResearchList from './components/ResearchList';
import ResearchDetails from './components/ResearchDetails';
import EnhancedResearchView from './components/EnhancedResearchView';

function App() {
  const [selectedResearchId, setSelectedResearchId] = useState<number | null>(null);
  const [useEnhancedView, setUseEnhancedView] = useState(true);
  const { data: researchList } = useResearchList();

  // Auto-select latest research on load
  useEffect(() => {
    if (researchList?.research_list?.length > 0 && !selectedResearchId) {
      setSelectedResearchId(researchList.research_list[0].id);
    }
  }, [researchList, selectedResearchId]);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Research Assistant</h1>
          
          {/* View Toggle */}
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">View:</span>
            <button
              onClick={() => setUseEnhancedView(false)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                !useEnhancedView 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Basic
            </button>
            <button
              onClick={() => setUseEnhancedView(true)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                useEnhancedView 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Enhanced
            </button>
          </div>
        </div>
        
        <ResearchForm onNewResearch={(id) => setSelectedResearchId(id)} />
        
        <ResearchList 
          researchList={researchList} 
          selectedId={selectedResearchId} 
          onSelect={setSelectedResearchId} 
        />

        {/* Conditional rendering based on view type */}
        {selectedResearchId && (
          useEnhancedView ? (
            <EnhancedResearchView researchId={selectedResearchId} />
          ) : (
            <ResearchDetails researchId={selectedResearchId} />
          )
        )}
      </div>
    </div>
  );
}

export default App;
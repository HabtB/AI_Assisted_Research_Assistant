import { useState } from 'react';
import { useStartResearch, useResearchStatus, useResearchList } from './hooks/useResearch';

function App() {
  const [query, setQuery] = useState('');
  const [researchId, setResearchId] = useState<number | null>(null);
  
  const startResearch = useStartResearch();
  const { data: statusData } = useResearchStatus(researchId);
  const { data: researchList } = useResearchList();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      const result = await startResearch.mutateAsync({
        query: query.trim(),
        max_results: 5,
        include_summary: true,
        language: 'en',
      });
      
      setResearchId(result.research.id);
      setQuery('');
    } catch (error) {
      console.error('Failed to start research:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">Research Assistant</h1>
        
        {/* Research Form */}
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your research query..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={startResearch.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {startResearch.isPending ? 'Starting...' : 'Start Research'}
            </button>
          </div>
        </form>

        {/* Status Display */}
        {statusData && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-semibold mb-4">Current Research Status</h2>
            <p>Status: <span className="font-medium">{statusData.status}</span></p>
            {statusData.task_info && (
              <p>Progress: {(statusData.task_info.task_info as { current_action?: string })?.current_action || 'Processing...'}</p>
            )}
          </div>
        )}

        {/* Research List */}
        {researchList && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Recent Research</h2>
            <div className="space-y-3">
              {researchList.research_list.map((research) => (
                <div key={research.id} className="border-b pb-3">
                  <p className="font-medium">{research.query}</p>
                  <p className="text-sm text-gray-600">
                    Status: {research.status} | Created: {new Date(research.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
import { useState } from 'react';
import { useStartResearch } from '../hooks/useResearch';

interface ResearchFormProps {
  onNewResearch: (id: number) => void;
}

const ResearchForm: React.FC<ResearchFormProps> = ({ onNewResearch }) => {
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(20);
  const [yearFrom, setYearFrom] = useState('');
  const [minCitations, setMinCitations] = useState(0);
  const [sources, setSources] = useState({
    semantic_scholar: true,
    pubmed: true,
    arxiv: true,
    crossref: true
  });
  
  const startResearch = useStartResearch();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const selectedSources = Object.entries(sources)
      .filter(([_, selected]) => selected)
      .map(([source, _]) => source);

    try {
      const result = await startResearch.mutateAsync({
        query: query.trim(),
        max_results: maxResults,
        include_summary: true,
        language: 'en',
        source_types: ['academic'],
        date_from: yearFrom || undefined,
        min_citations: minCitations,
        sources: selectedSources
      });
      
      onNewResearch(result.research.id);
      // Don't clear form after submission to allow easy modifications
    } catch (error) {
      console.error('Failed to start research:', error);
    }
  };

  const handleSourceChange = (source: string) => {
    setSources(prev => ({
      ...prev,
      [source]: !prev[source as keyof typeof prev]
    }));
  };

  return (
    <div className="mb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-t-lg p-8 text-white text-center">
        <div className="flex items-center justify-center mb-4">
          <span className="text-4xl mr-3">🎓</span>
          <h1 className="text-3xl font-bold">Academic Paper Search</h1>
        </div>
        <p className="text-lg opacity-90">Search across Semantic Scholar, PubMed, arXiv, and CrossRef</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-b-lg shadow-lg p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Search Query */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., machine learning, climate change..."
              className="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Form Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Max Results */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Results
              </label>
              <input
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 20)}
                min="1"
                max="100"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Year From */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Year From
              </label>
              <input
                type="text"
                value={yearFrom}
                onChange={(e) => setYearFrom(e.target.value)}
                placeholder="e.g., 2020"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Min Citations */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Citations
            </label>
            <input
              type="number"
              value={minCitations}
              onChange={(e) => setMinCitations(parseInt(e.target.value) || 0)}
              min="0"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Sources */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Sources
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(sources).map(([source, checked]) => (
                <label key={source} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => handleSourceChange(source)}
                    className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {source.replace('_', ' ')}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={startResearch.isPending || !query.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-lg text-lg font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <span className="text-2xl">🔍</span>
              <span>{startResearch.isPending ? 'Searching Papers...' : 'Search Papers'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResearchForm;
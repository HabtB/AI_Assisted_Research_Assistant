import React, { useState } from 'react';
import { 
  useResearchDetails, 
  useResearchSummary, 
  useFilteredResearch, 
  useExportResearch 
} from '../hooks/useResearch';

interface EnhancedResearchViewProps {
  researchId: number;
}

interface FilterState {
  year_from?: number;
  year_to?: number;
  min_citations?: number;
  venues?: string;
  has_pdf?: boolean;
}

const EnhancedResearchView: React.FC<EnhancedResearchViewProps> = ({ researchId }) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({});
  const [filteredResults, setFilteredResults] = useState<any>(null);

  const { data: research, isLoading: researchLoading } = useResearchDetails(researchId);
  const { data: summary, isLoading: summaryLoading } = useResearchSummary(researchId);
  const filterMutation = useFilteredResearch();
  const exportMutation = useExportResearch();

  const handleFilter = async () => {
    try {
      const result = await filterMutation.mutateAsync({
        id: researchId,
        filters
      });
      setFilteredResults(result);
    } catch (error) {
      console.error('Filter failed:', error);
    }
  };

  const handleExport = async (format: 'csv' | 'json' | 'excel' | 'bibtex') => {
    try {
      await exportMutation.mutateAsync({
        id: researchId,
        format
      });
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const resetFilters = () => {
    setFilters({});
    setFilteredResults(null);
  };

  if (researchLoading) {
    return <div className="flex justify-center p-8">Loading research...</div>;
  }

  if (!research) {
    return <div className="text-red-500 p-4">Research not found</div>;
  }

  const displayResults = filteredResults?.results || research.sources || [];
  const totalResults = filteredResults?.total_results || research.sources?.length || 0;
  const filteredCount = filteredResults?.filtered_results || totalResults;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">{research.query}</h1>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            research.status === 'completed' ? 'bg-green-100 text-green-800' :
            research.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {research.status}
          </span>
          <span>Created: {new Date(research.created_at).toLocaleDateString()}</span>
          {research.completed_at && (
            <span>Completed: {new Date(research.completed_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {/* Summary Report */}
      {summary && !summaryLoading && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">📊 Research Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{summary.total_papers}</div>
              <div className="text-sm text-gray-600">Total Papers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{summary.papers_with_pdf}</div>
              <div className="text-sm text-gray-600">With PDF</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{Math.round(summary.avg_citations)}</div>
              <div className="text-sm text-gray-600">Avg Citations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{summary.date_range}</div>
              <div className="text-sm text-gray-600">Date Range</div>
            </div>
          </div>
          
          {/* Top Venues */}
          {summary.top_venues && Object.keys(summary.top_venues).length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium mb-2">Top Venues:</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.top_venues).slice(0, 5).map(([venue, count]) => (
                  <span key={venue} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {venue} ({count as number})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sources */}
          {summary.sources && (
            <div>
              <h3 className="font-medium mb-2">Sources:</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(summary.sources).map(([source, count]) => (
                  <span key={source} className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                    {source} ({count as number})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Export and Filter Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Research Results</h2>
            <p className="text-sm text-gray-600">
              {filteredResults ? 
                `Showing ${filteredCount} of ${totalResults} results (filtered)` :
                `${totalResults} results found`
              }
            </p>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {/* Export Buttons */}
            <div className="flex gap-1">
              <button
                onClick={() => handleExport('csv')}
                disabled={exportMutation.isPending}
                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600 disabled:opacity-50"
              >
                CSV
              </button>
              <button
                onClick={() => handleExport('json')}
                disabled={exportMutation.isPending}
                className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50"
              >
                JSON
              </button>
              <button
                onClick={() => handleExport('excel')}
                disabled={exportMutation.isPending}
                className="px-3 py-1 bg-orange-500 text-white rounded text-sm hover:bg-orange-600 disabled:opacity-50"
              >
                Excel
              </button>
              <button
                onClick={() => handleExport('bibtex')}
                disabled={exportMutation.isPending}
                className="px-3 py-1 bg-purple-500 text-white rounded text-sm hover:bg-purple-600 disabled:opacity-50"
              >
                BibTeX
              </button>
            </div>
            
            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year From</label>
                <input
                  type="number"
                  value={filters.year_from || ''}
                  onChange={(e) => setFilters({...filters, year_from: e.target.value ? parseInt(e.target.value) : undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., 2020"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year To</label>
                <input
                  type="number"
                  value={filters.year_to || ''}
                  onChange={(e) => setFilters({...filters, year_to: e.target.value ? parseInt(e.target.value) : undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., 2024"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Citations</label>
                <input
                  type="number"
                  value={filters.min_citations || ''}
                  onChange={(e) => setFilters({...filters, min_citations: e.target.value ? parseInt(e.target.value) : undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., 10"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Venues (comma-separated)</label>
                <input
                  type="text"
                  value={filters.venues || ''}
                  onChange={(e) => setFilters({...filters, venues: e.target.value || undefined})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="e.g., Nature, Science, arXiv"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="has_pdf"
                  checked={filters.has_pdf || false}
                  onChange={(e) => setFilters({...filters, has_pdf: e.target.checked || undefined})}
                  className="mr-2"
                />
                <label htmlFor="has_pdf" className="text-sm font-medium text-gray-700">
                  Only papers with PDF
                </label>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={handleFilter}
                disabled={filterMutation.isPending}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {filterMutation.isPending ? 'Filtering...' : 'Apply Filters'}
              </button>
              <button
                onClick={resetFilters}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Reset
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      <div className="space-y-4">
        {displayResults.map((source: any, index: number) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-semibold text-gray-800 flex-1">
                {source.title}
              </h3>
              <div className="flex items-center space-x-2 ml-4">
                {source.citation_count > 0 && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                    {source.citation_count} citations
                  </span>
                )}
                {source.has_pdf && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                    PDF
                  </span>
                )}
              </div>
            </div>
            
            <div className="text-sm text-gray-600 mb-2">
              <span className="font-medium">Authors:</span> {
                Array.isArray(source.authors) ? source.authors.join(', ') : source.authors || 'N/A'
              }
            </div>
            
            <div className="text-sm text-gray-600 mb-2">
              <span className="font-medium">Year:</span> {source.year || 'N/A'} | 
              <span className="font-medium ml-2">Venue:</span> {source.venue || 'N/A'} |
              <span className="font-medium ml-2">Source:</span> {source.source || 'N/A'}
            </div>
            
            {source.abstract && (
              <p className="text-gray-700 mb-3">
                {source.abstract.length > 300 ? 
                  `${source.abstract.substring(0, 300)}...` : 
                  source.abstract
                }
              </p>
            )}
            
            <div className="flex items-center space-x-4 text-sm">
              {source.url && (
                <a 
                  href={source.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800"
                >
                  📄 View Paper
                </a>
              )}
              {source.doi && (
                <a 
                  href={`https://doi.org/${source.doi}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800"
                >
                  🔗 DOI
                </a>
              )}
              {source.relevance_score && (
                <span className="text-gray-500">
                  Relevance: {(source.relevance_score * 100).toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {displayResults.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No results found with current filters.
        </div>
      )}
    </div>
  );
};

export default EnhancedResearchView;

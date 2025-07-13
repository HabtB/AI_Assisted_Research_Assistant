import { useResearchDetails } from '../hooks/useResearch';
import jsPDF from 'jspdf';
import Papa from 'papaparse';

interface ResearchDetailsProps {
  researchId: number | null;
}

const ResearchDetails: React.FC<ResearchDetailsProps> = ({ researchId }) => {
  const { data: research, isLoading } = useResearchDetails(researchId);

  if (isLoading) return <p>Loading details...</p>;
  if (!research) return <p>Select a research to view details.</p>;

  // Compute summary report (similar to enhanced code)
  const createSummaryReport = (sources: any[]) => {
    const years = sources.map(s => s.year).filter(y => y);
    return {
      total_papers: sources.length,
      date_range: years.length ? `${Math.min(...years)}-${Math.max(...years)}` : 'N/A',
      sources: sources.reduce((acc, s) => {
        acc[s.source] = (acc[s.source] || 0) + 1;
        return acc;
      }, {}),
      top_venues: sources.reduce((acc, s) => {
        acc[s.venue] = (acc[s.venue] || 0) + 1;
        return acc;
      }, {}),
      avg_citations: sources.reduce((acc, s) => acc + s.citation_count, 0) / sources.length || 0,
      papers_with_pdf: sources.filter(s => s.pdf_url).length,
      top_cited: sources.sort((a, b) => b.citation_count - a.citation_count).slice(0, 5).map(s => ({
        title: s.title,
        citation_count: s.citation_count,
        year: s.year
      }))
    };
  };

  const report = createSummaryReport(research.sources || []);

  const handleExportPDF = () => {
    const doc = new jsPDF();
    doc.text(`Research: ${research.query}`, 10, 10);
    doc.text('Summary:', 10, 20);
    doc.text(research.summary || 'N/A', 10, 30, { maxWidth: 180 });
    doc.save(`${research.query}.pdf`);
  };

  const handleExportCSV = () => {
    const csvData = research.sources.map((source: any) => ({
      Title: source.title,
      URL: source.url,
      Summary: source.summary,
      DOI: source.doi,
      Citations: source.citation_count,
    }));
    const csv = Papa.unparse(csvData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${research.query}_sources.csv`;
    link.click();
  };

  const handleExportBibtex = () => {
    let bibtex = '';
    research.sources.forEach((paper, idx) => {
      const entry_type = paper.venue ? 'article' : 'misc';
      const key = paper.title.toLowerCase().replace(/[^\w]/g, '').slice(0, 20) + paper.year;
      bibtex += `@${entry_type}{${key},\n`;
      bibtex += `  title = {${paper.title}},\n`;
      if (paper.authors?.length) bibtex += `  author = {${paper.authors.join(' and ')}},\n`;
      if (paper.year) bibtex += `  year = {${paper.year}},\n`;
      if (paper.venue) bibtex += `  journal = {${paper.venue}},\n`;
      if (paper.doi) bibtex += `  doi = {${paper.doi}},\n`;
      if (paper.pdf_url) bibtex += `  url = {${paper.pdf_url}},\n`;
      bibtex = bibtex.trimEnd(', \n') + '\n}\n\n';
    });
    const blob = new Blob([bibtex], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${research.query}.bib`;
    link.click();
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Research Details: {research.query}</h2>
      
      {/* Summary Report */}
      <h3 className="text-lg font-medium mb-2">Summary Report</h3>
      <div className="grid grid-cols-2 gap-4 mb-6">
        <p>Total Papers: {report.total_papers}</p>
        <p>Date Range: {report.date_range}</p>
        <p>Avg Citations: {report.avg_citations.toFixed(1)}</p>
        <p>Papers with PDF: {report.papers_with_pdf}</p>
      </div>
      <h4 className="text-md font-medium mb-1">Top Venues</h4>
      <ul className="list-disc pl-5 mb-4">
        {Object.entries(report.top_venues).map(([venue, count]) => (
          <li key={venue}>{venue}: {count}</li>
        ))}
      </ul>
      <h4 className="text-md font-medium mb-1">Sources Distribution</h4>
      <ul className="list-disc pl-5 mb-6">
        {Object.entries(report.sources).map(([source, count]) => (
          <li key={source}>{source}: {count}</li>
        ))}
      </ul>
      <h4 className="text-md font-medium mb-1">Top Cited Papers</h4>
      <ul className="list-disc pl-5 mb-6">
        {report.top_cited.map((paper, idx) => (
          <li key={idx}>{paper.title} ({paper.citation_count} citations, {paper.year})</li>
        ))}
      </ul>
      
      {/* Summary */}
      <h3 className="text-lg font-medium mb-2">Summary</h3>
      <p className="text-gray-700 mb-6">{research.summary || 'Not available yet.'}</p>
      
      {/* Key Findings */}
      {research.key_findings?.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Key Findings</h3>
          <ul className="list-disc pl-5 space-y-1">
            {research.key_findings.map((finding: string, index: number) => (
              <li key={index} className="text-gray-700">{finding}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Sources */}
      {research.sources?.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Sources ({research.sources.length})</h3>
          <div className="space-y-4">
            {research.sources.sort((a, b) => b.citation_count - a.citation_count)  // Sort by citations
              .map((source: any) => (
                <div key={source.id} className="border p-4 rounded-lg">
                  <p className="font-medium">{source.title}</p>
                  <p className="text-sm text-gray-600">Authors: {source.author || 'N/A'}</p>
                  <p className="text-sm text-gray-600">Year: {source.year} | Venue: {source.venue || 'N/A'}</p>
                  <p className="text-sm text-gray-600">Citations: {source.citation_count} | DOI: {source.doi || 'N/A'}</p>
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">View Source</a>
                  <p className="mt-2 text-gray-700">Abstract: {source.summary}</p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {research.metadata_info?.recommendations?.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-medium mb-2">Recommendations</h3>
          <ul className="list-disc pl-5 space-y-1">
            {research.metadata_info.recommendations.map((rec: string, index: number) => (
              <li key={index} className="text-gray-700">{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Export Buttons */}
      <div className="flex gap-4">
        <button onClick={handleExportPDF} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
          Export to PDF
        </button>
        <button onClick={handleExportCSV} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
          Export to CSV
        </button>
      </div>
    </div>
  );
};

export default ResearchDetails;
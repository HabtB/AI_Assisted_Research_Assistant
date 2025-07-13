interface ResearchListProps {
    researchList: any;  // Type based on your schema
    selectedId: number | null;
    onSelect: (id: number) => void;
  }
  
  const ResearchList: React.FC<ResearchListProps> = ({ researchList, selectedId, onSelect }) => {
    return researchList?.research_list?.length > 0 ? (
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">Recent Research</h2>
        <div className="space-y-3">
          {researchList.research_list.map((research: any) => (
            <div 
              key={research.id} 
              className={`border-b pb-3 cursor-pointer hover:bg-gray-50 ${selectedId === research.id ? 'bg-blue-50' : ''}`}
              onClick={() => onSelect(research.id)}
            >
              <p className="font-medium">{research.query}</p>
              <p className="text-sm text-gray-600">
                Status: {research.status} | Created: {new Date(research.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    ) : (
      <p className="text-gray-500 mb-8">No recent research available yet. Start one above!</p>
    );
  };
  
  export default ResearchList;
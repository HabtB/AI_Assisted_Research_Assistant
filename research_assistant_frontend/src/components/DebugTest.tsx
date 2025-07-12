import React, { useState } from 'react';
import { apiClient } from '../services/api';

export const DebugTest: React.FC = () => {
  const [testResult, setTestResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testBackendConnection = async () => {
    setLoading(true);
    try {
      console.log('Testing backend connection...');
      
      // Test 1: Direct API test endpoint
      const response = await apiClient.get('/test');
      console.log('Test endpoint response:', response.data);
      setTestResult(JSON.stringify(response.data, null, 2));
      
    } catch (error: any) {
      console.error('Backend test failed:', error);
      setTestResult(`Error: ${error.message}\nStatus: ${error.response?.status}\nData: ${JSON.stringify(error.response?.data, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  const testResearchList = async () => {
    setLoading(true);
    try {
      console.log('Testing research list endpoint...');
      
      const response = await apiClient.get('/research/');
      console.log('Research list response:', response.data);
      setTestResult(JSON.stringify(response.data, null, 2));
      
    } catch (error: any) {
      console.error('Research list test failed:', error);
      setTestResult(`Error: ${error.message}\nStatus: ${error.response?.status}\nData: ${JSON.stringify(error.response?.data, null, 2)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-yellow-100 p-4 rounded-lg mb-4">
      <h3 className="font-bold mb-2">Debug Tests</h3>
      <div className="space-x-2 mb-2">
        <button
          onClick={testBackendConnection}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {loading ? 'Testing...' : 'Test Backend'}
        </button>
        <button
          onClick={testResearchList}
          disabled={loading}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
        >
          {loading ? 'Testing...' : 'Test Research List'}
        </button>
      </div>
      <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto max-h-40">
        {testResult || 'Click a button to test backend connectivity'}
      </pre>
    </div>
  );
};

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Trash2 } from 'lucide-react';
import Input from '../shared/Input';
import Button from '../shared/Button';
import LoadingSpinner from '../shared/LoadingSpinner';
import Alert from '../shared/Alert';
import api from '../../api/client';

export default function DeleteRecordForm({ zone, existingRecords, isLoading, error, onRecordsChange }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedRecords, setSelectedRecords] = useState([]);

  // Debounce search query - wait 500ms after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery.trim());
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Server-side search when user has typed at least 2 characters
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['zone-records-search', zone, debouncedSearch],
    queryFn: async () => {
      console.log('[DeleteRecordForm] Searching for:', debouncedSearch);
      const result = await api.getZoneRecords(zone, debouncedSearch, 1000);
      console.log('[DeleteRecordForm] Search results:', result);
      return result;
    },
    enabled: debouncedSearch.length >= 2,
    staleTime: 60000,
  });

  // Determine which records to display
  let displayRecords = [];
  let showSearchPrompt = false;
  
  if (debouncedSearch.length >= 2) {
    displayRecords = searchResults?.records || [];
  } else if (searchQuery.length > 0 && searchQuery.length < 2) {
    showSearchPrompt = true;
  } else {
    displayRecords = existingRecords;
  }

  const handleCheckboxChange = (record) => {
    const isSelected = selectedRecords.find(
      (r) => r.name === record.name && r.type === record.type
    );

    if (isSelected) {
      const updated = selectedRecords.filter(
        (r) => !(r.name === record.name && r.type === record.type)
      );
      setSelectedRecords(updated);
      onRecordsChange(updated.map((r) => ({ type: r.type, label: r.name, value: r.value })));
    } else {
      if (selectedRecords.length >= 5) {
        alert('Maximum 5 records can be selected');
        return;
      }
      const updated = [...selectedRecords, record];
      setSelectedRecords(updated);
      onRecordsChange(updated.map((r) => ({ type: r.type, label: r.name, value: r.value })));
    }
  };

  if (isLoading) {
    return <LoadingSpinner text="Loading existing records..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Failed to load records">
        <div className="space-y-2">
          <p>{error.message || 'An error occurred while fetching records'}</p>
          <p className="text-xs">Zone: {zone}</p>
          <p className="text-xs">Please check the browser console for details or contact support.</p>
        </div>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Alert variant="warning" title="Caution">
        Deletion is permanent and cannot be undone. Selected records will be removed from Azure DNS.
      </Alert>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <Input
          type="text"
          placeholder="Search records to delete (min 2 chars for server-side search)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {showSearchPrompt && (
        <Alert variant="info">
          Type at least 2 characters to search across all available records.
        </Alert>
      )}

      {searchLoading && (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" />
          <span className="ml-3 text-gray-600">Searching...</span>
        </div>
      )}

      {!searchLoading && displayRecords.length === 0 && !showSearchPrompt ? (
        <Alert variant="info">
          {debouncedSearch ? `No records found matching "${debouncedSearch}"` : 'No records found in this zone.'}
        </Alert>
      ) : !searchLoading && !showSearchPrompt ? (
        <>
          {debouncedSearch && searchResults && (
            <div className="text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded-lg p-3">
              Found {displayRecords.length} record{displayRecords.length !== 1 ? 's' : ''} matching "{debouncedSearch}"
              {searchResults.is_limited && <span className="text-blue-700 font-medium"> (showing first 1000)</span>}
            </div>
          )}
          <div className="border rounded-lg overflow-hidden max-h-96 overflow-y-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="w-12 px-4 py-3"></th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Value
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    TTL
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayRecords.map((record, index) => {
                  const isSelected = selectedRecords.find(
                    (r) => r.name === record.name && r.type === record.type
                  );
                  const fqdn = record.name === '@' ? zone : `${record.name}.${zone}`;
                  return (
                    <tr
                      key={index}
                      className={`hover:bg-gray-50 ${isSelected ? 'bg-red-50' : ''}`}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          className="w-4 h-4 text-red-600 rounded"
                          checked={!!isSelected}
                          onChange={() => handleCheckboxChange(record)}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded">
                          {record.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-sm">
                        <div className="text-gray-900">{fqdn}</div>
                        <div className="text-xs text-gray-500">({record.name})</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                        {record.value}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{record.ttl}s</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {selectedRecords.length > 0 && (
            <Alert variant="error" title="Records Staged for Deletion">
              <div className="space-y-2">
                <p className="font-semibold">
                  {selectedRecords.length} record(s) will be permanently deleted:
                </p>
                <ul className="list-disc list-inside space-y-1">
                  {selectedRecords.map((record, index) => {
                    const fqdn = record.name === '@' ? zone : `${record.name}.${zone}`;
                    return (
                      <li key={index} className="text-sm">
                        <strong>{record.type}</strong> - {fqdn} → {record.value}
                      </li>
                    );
                  })}
                </ul>
              </div>
            </Alert>
          )}
        </>
      ) : null}
    </div>
  );
}

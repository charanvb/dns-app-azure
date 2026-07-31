import { useState } from 'react';
import { Search, Trash2 } from 'lucide-react';
import Input from '../shared/Input';
import Button from '../shared/Button';
import LoadingSpinner from '../shared/LoadingSpinner';
import Alert from '../shared/Alert';

export default function DeleteRecordForm({ zone, existingRecords, isLoading, onRecordsChange }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecords, setSelectedRecords] = useState([]);

  const filteredRecords = existingRecords.filter((record) =>
    `${record.name} ${record.type} ${record.value}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  return (
    <div className="space-y-6">
      <Alert variant="warning" title="Caution">
        Deletion is permanent and cannot be undone. Selected records will be removed from Azure DNS.
      </Alert>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <Input
          type="text"
          placeholder="Search records to delete..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {existingRecords.length === 0 ? (
        <Alert variant="info">No records found in this zone.</Alert>
      ) : (
        <>
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
                {filteredRecords.map((record, index) => {
                  const isSelected = selectedRecords.find(
                    (r) => r.name === record.name && r.type === record.type
                  );
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
                      <td className="px-4 py-3 font-medium">{record.name}</td>
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
                  {selectedRecords.map((record, index) => (
                    <li key={index} className="text-sm">
                      <strong>{record.type}</strong> - {record.name} → {record.value}
                    </li>
                  ))}
                </ul>
              </div>
            </Alert>
          )}
        </>
      )}
    </div>
  );
}

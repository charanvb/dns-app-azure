import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import Input from '../shared/Input';
import LoadingSpinner from '../shared/LoadingSpinner';
import Alert from '../shared/Alert';

export default function ModifyRecordForm({ zone, existingRecords, isLoading, onRecordsChange }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [stagedRecords, setStagedRecords] = useState([]);

  const filteredRecords = existingRecords.filter((record) =>
    `${record.name} ${record.type} ${record.value}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCheckboxChange = (record) => {
    const isSelected = selectedRecords.find(
      (r) => r.name === record.name && r.type === record.type
    );

    if (isSelected) {
      setSelectedRecords(selectedRecords.filter(
        (r) => !(r.name === record.name && r.type === record.type)
      ));
    } else {
      if (selectedRecords.length >= 5) {
        alert('Maximum 5 records can be selected');
        return;
      }
      setSelectedRecords([...selectedRecords, record]);
    }
  };

  const stageForModification = () => {
    const staged = selectedRecords.map((record) => ({
      type: record.type,
      label: record.name,
      currentValue: record.value,
      newValue: record.value,
      ttl: record.ttl || 300,
    }));

    setStagedRecords(staged);
    setSelectedRecords([]);
  };

  const updateStagedRecord = (index, field, value) => {
    const updated = [...stagedRecords];
    updated[index] = { ...updated[index], [field]: value };
    setStagedRecords(updated);

    // Pass valid records to parent
    const valid = updated.filter((r) => r.newValue && r.newValue !== r.currentValue);
    onRecordsChange(valid);
  };

  const removeStagedRecord = (index) => {
    const updated = stagedRecords.filter((_, i) => i !== index);
    setStagedRecords(updated);
    onRecordsChange(updated.filter((r) => r.newValue && r.newValue !== r.currentValue));
  };

  if (isLoading) {
    return <LoadingSpinner text="Loading existing records..." />;
  }

  return (
    <div className="space-y-6">
      {/* Existing Records Selection */}
      {stagedRecords.length === 0 && (
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search existing records..."
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
                    {filteredRecords.map((record, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            className="w-4 h-4 text-primary-600 rounded"
                            checked={selectedRecords.some(
                              (r) => r.name === record.name && r.type === record.type
                            )}
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
                    ))}
                  </tbody>
                </table>
              </div>

              {selectedRecords.length > 0 && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={stageForModification}
                    className="btn btn-primary"
                  >
                    Stage {selectedRecords.length} Record(s) for Modification
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Staged Records for Modification */}
      {stagedRecords.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-semibold text-gray-900">Records to Modify</h3>

          {stagedRecords.map((record, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-4 border-2 border-gray-200">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded mr-2">
                    {record.type}
                  </span>
                  <span className="font-medium">{record.label}</span>
                </div>
                <button
                  type="button"
                  onClick={() => removeStagedRecord(index)}
                  className="text-red-600 hover:text-red-700 text-sm"
                >
                  Remove
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Current Value
                  </label>
                  <div className="px-3 py-2 bg-gray-200 rounded text-sm text-gray-700 break-all">
                    {record.currentValue}
                  </div>
                </div>

                <Input
                  label="New Value"
                  required
                  value={record.newValue}
                  onChange={(e) => updateStagedRecord(index, 'newValue', e.target.value)}
                  placeholder="Enter new value"
                />

                <Input
                  label="TTL (seconds)"
                  required
                  type="number"
                  value={record.ttl}
                  onChange={(e) =>
                    updateStagedRecord(index, 'ttl', parseInt(e.target.value, 10))
                  }
                  min={60}
                  max={86400}
                />
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={() => setStagedRecords([])}
            className="btn btn-secondary text-sm"
          >
            ← Back to Selection
          </button>
        </div>
      )}
    </div>
  );
}

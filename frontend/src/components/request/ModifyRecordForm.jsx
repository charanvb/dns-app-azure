import { useState, useEffect } from 'react';
import { Search, Plus, X } from 'lucide-react';
import Input from '../shared/Input';
import LoadingSpinner from '../shared/LoadingSpinner';
import Alert from '../shared/Alert';

export default function ModifyRecordForm({ zone, existingRecords, isLoading, onRecordsChange }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [stagedRecords, setStagedRecords] = useState([]);

  const filteredRecords = existingRecords.filter((record) => {
    const fqdn = record.name === '@' ? zone : `${record.name}.${zone}`;
    return `${fqdn} ${record.type} ${record.value}`.toLowerCase().includes(searchQuery.toLowerCase());
  });

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
    const staged = selectedRecords.map((record) => {
      // For TXT records, split pipe-separated values into array
      let txtValues = [];
      if (record.type === 'TXT') {
        txtValues = record.value.includes('|') 
          ? record.value.split('|').map(v => v.trim()).filter(v => v)
          : [record.value];
      }

      return {
        type: record.type,
        label: record.name,
        currentValue: record.value,
        newValue: record.type === 'TXT' ? '' : record.value,
        txtValues: record.type === 'TXT' ? [...txtValues] : [],
        ttl: record.ttl || 300,
      };
    });

    setStagedRecords(staged);
    setSelectedRecords([]);
  };

  const updateStagedRecord = (index, field, value) => {
    const updated = [...stagedRecords];
    updated[index] = { ...updated[index], [field]: value };
    setStagedRecords(updated);

    // Pass valid records to parent - for TXT, join txtValues with pipe
    const valid = updated.map(r => {
      if (r.type === 'TXT') {
        const joinedValue = r.txtValues.filter(v => v.trim()).join('|');
        return { ...r, newValue: joinedValue };
      }
      return r;
    }).filter((r) => r.newValue && r.newValue !== r.currentValue);
    
    onRecordsChange(valid);
  };

  const addTxtValue = (index) => {
    const updated = [...stagedRecords];
    updated[index].txtValues = [...updated[index].txtValues, ''];
    setStagedRecords(updated);
  };

  const removeTxtValue = (recordIndex, valueIndex) => {
    const updated = [...stagedRecords];
    updated[recordIndex].txtValues = updated[recordIndex].txtValues.filter((_, i) => i !== valueIndex);
    setStagedRecords(updated);
    updateStagedRecord(recordIndex, 'txtValues', updated[recordIndex].txtValues);
  };

  const updateTxtValue = (recordIndex, valueIndex, value) => {
    const updated = [...stagedRecords];
    updated[recordIndex].txtValues[valueIndex] = value;
    setStagedRecords(updated);
    updateStagedRecord(recordIndex, 'txtValues', updated[recordIndex].txtValues);
  };

  const removeStagedRecord = (index) => {
    const updated = stagedRecords.filter((_, i) => i !== index);
    setStagedRecords(updated);
    
    const valid = updated.map(r => {
      if (r.type === 'TXT') {
        const joinedValue = r.txtValues.filter(v => v.trim()).join('|');
        return { ...r, newValue: joinedValue };
      }
      return r;
    }).filter((r) => r.newValue && r.newValue !== r.currentValue);
    
    onRecordsChange(valid);
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
                    {filteredRecords.map((record, index) => {
                      const fqdn = record.name === '@' ? zone : `${record.name}.${zone}`;
                      return (
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

          {stagedRecords.map((record, index) => {
            const fqdn = record.label === '@' ? zone : `${record.label}.${zone}`;
            return (
              <div key={index} className="bg-gray-50 rounded-lg p-4 border-2 border-gray-200">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded mr-2">
                      {record.type}
                    </span>
                    <span className="font-medium">{fqdn}</span>
                    <span className="text-xs text-gray-500 ml-2">({record.label})</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeStagedRecord(index)}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    Remove
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Current Value
                    </label>
                    <div className="px-3 py-2 bg-gray-200 rounded text-sm text-gray-700 break-all">
                      {record.currentValue}
                    </div>
                  </div>

                  {record.type === 'TXT' ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        New TXT Values (each value in separate box)
                      </label>
                      <div className="space-y-2">
                        {record.txtValues.map((txtValue, valueIndex) => (
                          <div key={valueIndex} className="flex gap-2">
                            <Input
                              value={txtValue}
                              onChange={(e) => updateTxtValue(index, valueIndex, e.target.value)}
                              placeholder={`TXT value ${valueIndex + 1}`}
                              className="flex-1"
                            />
                            {record.txtValues.length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeTxtValue(index, valueIndex)}
                                className="px-3 py-2 text-red-600 hover:bg-red-50 rounded border border-red-200"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => addTxtValue(index)}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded border border-primary-200"
                        >
                          <Plus className="w-4 h-4" />
                          Add Another TXT Value
                        </button>
                      </div>
                    </div>
                  ) : (
                    <Input
                      label="New Value"
                      required
                      value={record.newValue}
                      onChange={(e) => updateStagedRecord(index, 'newValue', e.target.value)}
                      placeholder="Enter new value"
                    />
                  )}

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
            );
          })}

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

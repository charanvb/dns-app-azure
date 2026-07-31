import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import Button from '../shared/Button';
import Input from '../shared/Input';
import Select from '../shared/Select';
import Alert from '../shared/Alert';

const RECORD_TYPES = [
  { value: 'A', label: 'A (IPv4 Address)' },
  { value: 'AAAA', label: 'AAAA (IPv6 Address)' },
  { value: 'CNAME', label: 'CNAME (Alias)' },
  { value: 'TXT', label: 'TXT (Text Record)' },
];

const RECORD_PLACEHOLDERS = {
  A: '203.0.113.10',
  AAAA: '2001:db8::1',
  CNAME: 'target.example.com',
  TXT: 'v=spf1 include:example.com -all',
};

const RECORD_HINTS = {
  A: 'IPv4 address only (e.g., 203.0.113.10)',
  AAAA: 'IPv6 address only (e.g., 2001:db8::1)',
  CNAME: 'Fully qualified domain name only (e.g., target.example.com)',
  TXT: 'Any text - supports multiple values',
};

const validateIPv4 = (value) => {
  const parts = value.split('.');
  return parts.length === 4 && parts.every(p => {
    const n = parseInt(p, 10);
    return n >= 0 && n <= 255 && p === n.toString();
  });
};

const validateIPv6 = (value) => /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/.test(value);

const validateFQDN = (value) => /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/.test(value);

export default function CreateRecordForm({ zone, existingRecords = [], onRecordsChange }) {
  const [records, setRecords] = useState([]);

  // Helper to check if SPF record exists
  const hasSPF = (label) => {
    return existingRecords.some(r => 
      r.name === label && 
      r.type === 'TXT' && 
      (r.value || '').toLowerCase().includes('v=spf1')
    );
  };

  // Helper to check if record with same label and type exists
  const recordExists = (label, type) => {
    return existingRecords.some(r => r.name === label && r.type === type);
  };

  // Helper to check for duplicate labels in current records
  const hasDuplicateInRecords = (currentId, label, type) => {
    return records.some(r => r.id !== currentId && r.label === label && r.type === type);
  };

  const addRecord = () => {
    if (records.length >= 5) {
      alert('Maximum 5 records per request');
      return;
    }

    const newRecord = {
      id: Date.now(),
      type: 'A',
      label: '',
      value: '',
      txtValues: [''], // For TXT records with multiple values
      ttl: 300,
      error: null,
    };

    const updated = [...records, newRecord];
    setRecords(updated);
    updateValidRecords(updated);
  };

  const removeRecord = (id) => {
    const updated = records.filter((r) => r.id !== id);
    setRecords(updated);
    updateValidRecords(updated);
  };

  const addTxtValue = (id) => {
    const updated = records.map((r) => {
      if (r.id !== id) return r;
      return { ...r, txtValues: [...r.txtValues, ''] };
    });
    setRecords(updated);
    updateValidRecords(updated);
  };

  const removeTxtValue = (id, index) => {
    const updated = records.map((r) => {
      if (r.id !== id) return r;
      const newTxtValues = r.txtValues.filter((_, i) => i !== index);
      return { ...r, txtValues: newTxtValues.length > 0 ? newTxtValues : [''] };
    });
    setRecords(updated);
    updateValidRecords(updated);
  };

  const updateTxtValue = (id, index, value) => {
    const updated = records.map((r) => {
      if (r.id !== id) return r;
      const newTxtValues = [...r.txtValues];
      newTxtValues[index] = value;
      return { ...r, txtValues: newTxtValues, error: null };
    });
    setRecords(updated);
    updateValidRecords(updated);
  };

  const updateValidRecords = (currentRecords) => {
    const validRecords = currentRecords
      .filter((r) => {
        // For TXT: need at least one non-empty value
        if (r.type === 'TXT') {
          return !r.error && r.label && r.txtValues.some(v => v.trim());
        }
        // For other types: need value
        return !r.error && r.label && r.value;
      })
      .map((r) => {
        if (r.type === 'TXT') {
          // Filter out empty values and join with pipe
          const filteredValues = r.txtValues.filter(v => v.trim());
          return {
            type: r.type,
            label: r.label,
            value: filteredValues.join('|'), // Join with pipe for backend
            ttl: r.ttl
          };
        }
        return {
          type: r.type,
          label: r.label,
          value: r.value,
          ttl: r.ttl
        };
      });
    onRecordsChange(validRecords);
  };

  const updateRecord = (id, field, value) => {
    const updated = records.map((r) => {
      if (r.id !== id) return r;

      const updatedRecord = { ...r, [field]: value, error: null };

      // Clear txtValues when switching away from TXT
      if (field === 'type' && value !== 'TXT') {
        updatedRecord.txtValues = [''];
        updatedRecord.value = '';
      }

      // Strict validation based on record type
      if (field === 'value' && value) {
        if (r.type === 'A') {
          if (!validateIPv4(value)) {
            updatedRecord.error = 'A records must contain a valid IPv4 address only';
          }
        } else if (r.type === 'AAAA') {
          if (!validateIPv6(value)) {
            updatedRecord.error = 'AAAA records must contain a valid IPv6 address only';
          }
        } else if (r.type === 'CNAME') {
          if (!validateFQDN(value)) {
            updatedRecord.error = 'CNAME records must contain a valid fully qualified domain name only';
          }

        }
      }

      if (field === 'label' && value) {
        // Check for duplicate in existing records
        if (recordExists(value, r.type)) {
          updatedRecord.error = `A ${r.type} record with label "${value}" already exists in this zone`;
        }
        // Check for duplicate in current form
        else if (hasDuplicateInRecords(id, value, r.type)) {
          updatedRecord.error = `You already have a ${r.type} record with label "${value}" in this request`;
        }
        // Check for existing SPF record
        else if (r.type === 'TXT' && r.txtValues.some(v => v.toLowerCase().includes('v=spf1')) && hasSPF(value)) {
          updatedRecord.error = `An SPF record already exists for "${value}". Please modify the existing one instead`;
        }
        else if (value.includes('*')) {
          updatedRecord.error = 'Wildcards (*) are not permitted';
        } else if (value.length > 253) {
          updatedRecord.error = 'Label exceeds maximum length (253)';
        } else if (value !== '@' && !/^[a-zA-Z0-9][a-zA-Z0-9.\-]*$/.test(value)) {
          updatedRecord.error = 'Only a-z, 0-9, hyphens and dots allowed';
        }
      }

      // Check SPF when TXT value changes
      if (field === 'txtValues' || (r.type === 'TXT' && field === 'value')) {
        const txtValues = field === 'txtValues' ? value : r.txtValues;
        const hasSPFValue = txtValues.some(v => (v || '').toLowerCase().includes('v=spf1'));
        if (hasSPFValue && r.label && hasSPF(r.label)) {
          updatedRecord.error = `An SPF record already exists for "${r.label}". Please modify the existing one instead`;
        }
      }

      return updatedRecord;
    });

    setRecords(updated);
    updateValidRecords(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          Add up to 5 records. All fields are validated in real-time.
        </p>
        <Button type="button" size="sm" onClick={addRecord} disabled={records.length >= 5}>
          <Plus className="w-4 h-4" /> Add Record
        </Button>
      </div>

      {records.length === 0 && (
        <Alert variant="info">
          Click "Add Record" to start creating DNS records.
        </Alert>
      )}

      <div className="space-y-4">
        {records.map((record, index) => (
          <div key={record.id} className="bg-gray-50 rounded-lg p-4 border-2 border-gray-200">
            <div className="flex items-start justify-between mb-4">
              <h4 className="font-semibold text-gray-900">Record #{index + 1}</h4>
              <button
                type="button"
                onClick={() => removeRecord(record.id)}
                className="text-red-600 hover:text-red-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Record Type"
                required
                value={record.type}
                onChange={(e) => updateRecord(record.id, 'type', e.target.value)}
                options={RECORD_TYPES}
              />

              <Input
                label="Label"
                required
                hint='Use "@" for zone apex'
                value={record.label}
                onChange={(e) => updateRecord(record.id, 'label', e.target.value)}
                placeholder="subdomain or @"
              />

              {record.type === 'TXT' ? (
                <div className="md:col-span-2 space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    TXT Values <span className="text-red-500">*</span>
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    TXT records can have multiple values. Click "Add Value" to add more.
                  </p>
                  {record.txtValues.map((txtValue, txtIdx) => (
                    <div key={txtIdx} className="flex gap-2">
                      <input
                        type="text"
                        className="input flex-1"
                        placeholder={RECORD_PLACEHOLDERS.TXT}
                        value={txtValue}
                        onChange={(e) => updateTxtValue(record.id, txtIdx, e.target.value)}
                      />
                      {record.txtValues.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeTxtValue(record.id, txtIdx)}
                          className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => addTxtValue(record.id)}
                  >
                    <Plus className="w-4 h-4" /> Add TXT Value
                  </Button>
                </div>
              ) : (
                <Input
                  label="Value"
                  required
                  hint={RECORD_HINTS[record.type] || ''}
                  value={record.value}
                  onChange={(e) => updateRecord(record.id, 'value', e.target.value)}
                  placeholder={RECORD_PLACEHOLDERS[record.type]}
                  error={record.error}
                />
              )}

              <Input
                label="TTL (seconds)"
                required
                type="number"
                value={record.ttl}
                onChange={(e) => updateRecord(record.id, 'ttl', parseInt(e.target.value, 10))}
                min={60}
                max={86400}
              />
            </div>

            {record.type === 'TXT' && record.txtValues.some(v => v.toLowerCase().startsWith('v=spf1')) && (
              <Alert variant="warning" className="mt-3">
                SPF record detected. Ensure no existing SPF exists for this label to avoid mail
                delivery issues.
              </Alert>
            )}
            
            {record.error && (
              <Alert variant="error" className="mt-3">
                {record.error}
              </Alert>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

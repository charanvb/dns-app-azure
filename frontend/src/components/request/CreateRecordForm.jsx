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
  { value: 'SRV', label: 'SRV (Service Record)' },
];

const RECORD_PLACEHOLDERS = {
  A: '203.0.113.10',
  AAAA: '2001:db8::1',
  CNAME: 'target.example.com',
  TXT: 'v=spf1 include:example.com -all',
  SRV: 'svc.example.com',
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

export default function CreateRecordForm({ zone, onRecordsChange }) {
  const [records, setRecords] = useState([]);

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
      ttl: 300,
      error: null,
    };

    const updated = [...records, newRecord];
    setRecords(updated);
    onRecordsChange(updated);
  };

  const removeRecord = (id) => {
    const updated = records.filter((r) => r.id !== id);
    setRecords(updated);
    onRecordsChange(updated);
  };

  const updateRecord = (id, field, value) => {
    const updated = records.map((r) => {
      if (r.id !== id) return r;

      const updatedRecord = { ...r, [field]: value, error: null };

      // Validate on the fly
      if (field === 'value' && value) {
        if (r.type === 'A' && !validateIPv4(value)) {
          updatedRecord.error = 'Invalid IPv4 address';
        } else if (r.type === 'AAAA' && !validateIPv6(value)) {
          updatedRecord.error = 'Invalid IPv6 address';
        } else if (r.type === 'CNAME' && !validateFQDN(value)) {
          updatedRecord.error = 'Must be a fully qualified domain name';
        }
      }

      if (field === 'label' && value) {
        if (value.includes('*')) {
          updatedRecord.error = 'Wildcards (*) are not permitted';
        } else if (value.length > 253) {
          updatedRecord.error = 'Label exceeds maximum length (253)';
        } else if (value !== '@' && !/^[a-zA-Z0-9][a-zA-Z0-9.\-]*$/.test(value)) {
          updatedRecord.error = 'Only a-z, 0-9, hyphens and dots allowed';
        }
      }

      return updatedRecord;
    });

    setRecords(updated);
    onRecordsChange(updated.filter((r) => !r.error && r.label && r.value));
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

              <Input
                label="Value"
                required
                value={record.value}
                onChange={(e) => updateRecord(record.id, 'value', e.target.value)}
                placeholder={RECORD_PLACEHOLDERS[record.type]}
                error={record.error}
              />

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

            {record.type === 'TXT' && record.value.toLowerCase().startsWith('v=spf1') && (
              <Alert variant="warning" className="mt-3">
                SPF record detected. Ensure no existing SPF exists for this label to avoid mail
                delivery issues.
              </Alert>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

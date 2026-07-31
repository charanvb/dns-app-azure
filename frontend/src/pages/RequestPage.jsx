import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { ArrowRight, ArrowLeft, Search } from 'lucide-react';
import { api } from '../api/client';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';
import Input from '../components/shared/Input';
import Alert from '../components/shared/Alert';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import StepIndicator from '../components/request/StepIndicator';
import CreateRecordForm from '../components/request/CreateRecordForm';
import ModifyRecordForm from '../components/request/ModifyRecordForm';
import DeleteRecordForm from '../components/request/DeleteRecordForm';

const BLACKLISTED_DOMAINS = [
  'micetro.example.com',
  'unilever.com.cn',
  'unileverdigital.com',
  // Add more blocked domains here as needed
];

const RESTRICTED_DOMAINS = [
  // Domains that require Cloud Ops approval (warning only)
  // Example: 'critical.example.com',
];

export default function RequestPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedZone, setSelectedZone] = useState('');
  const [selectedAction, setSelectedAction] = useState('');
  const [recordsToSubmit, setRecordsToSubmit] = useState([]);
  
  const [zoneSearchQuery, setZoneSearchQuery] = useState('');
  const [zoneSearchResults, setZoneSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showZoneDropdown, setShowZoneDropdown] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm();

  const searchZones = useCallback(async (query) => {
    if (query.length < 2) {
      setZoneSearchResults([]);
      return;
    }
    
    setIsSearching(true);
    try {
      const result = await api.searchZones(query, 50);
      setZoneSearchResults(result.zones || []);
    } catch (error) {
      toast.error('Failed to search zones');
      setZoneSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleZoneSearch = (e) => {
    const query = e.target.value;
    setZoneSearchQuery(query);
    setShowZoneDropdown(true);
    
    if (query.length >= 2) {
      const timeoutId = setTimeout(() => searchZones(query), 300);
      return () => clearTimeout(timeoutId);
    } else {
      setZoneSearchResults([]);
    }
  };

  const selectZone = (zoneName) => {
    setSelectedZone(zoneName);
    setZoneSearchQuery(zoneName);
    setShowZoneDropdown(false);
  };

  const { data: existingRecords, isLoading: recordsLoading, error: recordsError } = useQuery({
    queryKey: ['zone-records', selectedZone],
    queryFn: async () => {
      console.log('[RequestPage] Fetching records for zone:', selectedZone);
      const result = await api.getZoneRecords(selectedZone);
      console.log('[RequestPage] Records received:', result);
      return result;
    },
    enabled: !!selectedZone && (selectedAction === 'modify' || selectedAction === 'delete' || selectedAction === 'create'),
    staleTime: 300000, // 5 minutes
    retry: 1, // Only retry once
  });

  const submitMutation = useMutation({
    mutationFn: (data) => api.submitRequest(data),
    onSuccess: (data) => {
      toast.success('DNS request submitted successfully!');
      navigate('/confirmation', {
        state: {
          results: data.results || [],
          zone: selectedZone,
          action: selectedAction,
          summary: data.summary || {},
          request_id: data.request_id || null,
        },
      });
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to submit request');
    },
  });

  const isZoneBlacklisted = BLACKLISTED_DOMAINS.some(
    (domain) => selectedZone.toLowerCase() === domain || selectedZone.toLowerCase().endsWith(`.${domain}`)
  );

  const isZoneRestricted = RESTRICTED_DOMAINS.some(
    (domain) => selectedZone.toLowerCase() === domain || selectedZone.toLowerCase().endsWith(`.${domain}`)
  );

  const steps = [
    { number: 1, name: 'Zone & Action' },
    { number: 2, name: 'Configure Records' },
    { number: 3, name: 'Review & Submit' },
  ];

  const handleNext = () => {
    if (currentStep === 1) {
      if (!selectedZone || !selectedAction) {
        toast.error('Please select both zone and action');
        return;
      }
      if (isZoneBlacklisted) {
        toast.error('This zone is managed via Micetro and cannot be changed here');
        return;
      }
    }
    setCurrentStep((prev) => Math.min(prev + 1, 3));
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const onSubmit = (formData) => {
    const payload = {
      zone: selectedZone,
      action: selectedAction,
      records: recordsToSubmit,
      justification: formData.justification,
    };

    submitMutation.mutate(payload);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">DNS Change Request</h1>
        <p className="mt-1 text-gray-600">
          Create, modify, or delete DNS records. One change set per request.
        </p>
      </div>

      <StepIndicator steps={steps} currentStep={currentStep} />

      <Card>
        <form onSubmit={handleSubmit(onSubmit)}>
          {currentStep === 1 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Select Zone and Action</h2>

              <div className="relative">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  DNS Zone <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-gray-500 mb-2">Start typing to search zones (min 2 characters)</p>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    className="input pl-10"
                    placeholder="Type to search zones..."
                    value={zoneSearchQuery}
                    onChange={handleZoneSearch}
                    onFocus={() => setShowZoneDropdown(true)}
                    onBlur={() => setTimeout(() => setShowZoneDropdown(false), 200)}
                  />
                </div>

                {showZoneDropdown && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
                    {isSearching ? (
                      <div className="px-4 py-3 text-center">
                        <LoadingSpinner size="sm" />
                      </div>
                    ) : zoneSearchResults.length > 0 ? (
                      <ul>
                        {zoneSearchResults.map((zone) => (
                          <li
                            key={zone.name}
                            className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                            onClick={() => selectZone(zone.name)}
                          >
                            <div className="font-medium">{zone.name}</div>
                            <div className="text-xs text-gray-500">
                              {zone.record_set_count} records • {zone.zone_type}
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="px-4 py-3 text-sm text-gray-500">
                        {zoneSearchQuery.length < 2 
                          ? 'Type at least 2 characters to search'
                          : 'No zones found matching your search'}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {selectedZone && isZoneBlacklisted && (
                <Alert variant="error" title="Zone Restricted">
                  This zone is managed via <strong>Micetro</strong> and cannot be changed through
                  this portal. Please raise your request there.
                </Alert>
              )}

              {selectedZone && isZoneRestricted && (
                <Alert variant="warning" title="Approval Required">
                  Changes to <strong>{selectedZone}</strong> require Cloud Ops approval. 
                  Please contact <a href="mailto:UL_cloudops@hcltech.com" className="underline">UL_cloudops@hcltech.com</a> before proceeding.
                </Alert>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action <span className="text-red-500">*</span>
                </label>
                <select
                  className="input"
                  value={selectedAction}
                  onChange={(e) => setSelectedAction(e.target.value)}
                >
                  <option value="">-- Select an action --</option>
                  <option value="create">Create DNS Record</option>
                  <option value="modify">Modify DNS Record</option>
                  <option value="delete">Delete DNS Record</option>
                </select>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleNext} disabled={!selectedZone || !selectedAction || isZoneBlacklisted}>
                  Next <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Configure Records</h2>
                <span className="text-sm text-gray-600">
                  Zone: <strong>{selectedZone}</strong> • Action:{' '}
                  <strong className="capitalize">{selectedAction}</strong>
                </span>
              </div>

              {selectedAction === 'create' && (
                <CreateRecordForm
                  zone={selectedZone}
                  existingRecords={existingRecords?.records || []}
                  onRecordsChange={setRecordsToSubmit}
                />
              )}

              {selectedAction === 'modify' && (
                <ModifyRecordForm
                  zone={selectedZone}
                  existingRecords={existingRecords?.records || []}
                  isLoading={recordsLoading}
                  error={recordsError}
                  onRecordsChange={setRecordsToSubmit}
                />
              )}

              {selectedAction === 'delete' && (
                <DeleteRecordForm
                  zone={selectedZone}
                  existingRecords={existingRecords?.records || []}
                  isLoading={recordsLoading}
                  error={recordsError}
                  onRecordsChange={setRecordsToSubmit}
                />
              )}

              <div className="flex justify-between pt-4 border-t">
                <Button type="button" variant="secondary" onClick={handleBack}>
                  <ArrowLeft className="w-4 h-4" /> Back
                </Button>
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={!recordsToSubmit.length}
                >
                  Review <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Review and Submit</h2>

              <div className="bg-gray-50 rounded-lg p-4">
                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="font-medium text-gray-600">Zone</dt>
                    <dd className="mt-1 font-semibold">{selectedZone}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-gray-600">Action</dt>
                    <dd className="mt-1 font-semibold capitalize">{selectedAction}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-gray-600">Record Count</dt>
                    <dd className="mt-1 font-semibold">{recordsToSubmit.length}</dd>
                  </div>
                </dl>
              </div>

              <div>
                <h3 className="font-semibold mb-3">Records to {selectedAction}</h3>
                <div className="border rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Type
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Label
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Value
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          TTL
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {recordsToSubmit.map((record, index) => {
                        const recordValue = record.value || record.newValue || '';
                        return (
                          <tr key={index}>
                            <td className="px-4 py-2">
                              <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded">
                                {record.type}
                              </span>
                            </td>
                            <td className="px-4 py-2 font-medium">{record.label || '@'}</td>
                            <td className="px-4 py-2 text-sm text-gray-600 max-w-md">
                              {record.type === 'TXT' && recordValue.includes('|') ? (
                                <div className="space-y-1">
                                  {recordValue.split('|').map((val, idx) => (
                                    <div key={idx} className="text-xs bg-gray-50 p-1 rounded">{val}</div>
                                  ))}
                                </div>
                              ) : (
                                <span className="break-all">{recordValue}</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-600">{record.ttl || 300}s</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <Input
                label="Business Justification"
                required
                hint="Minimum 20 characters"
                {...register('justification', {
                  required: 'Justification is required',
                  minLength: {
                    value: 20,
                    message: 'Justification must be at least 20 characters',
                  },
                })}
                error={errors.justification?.message}
                as="textarea"
                rows={3}
                placeholder="Explain the reason for this DNS change..."
              />

              <div className="flex justify-between pt-4 border-t">
                <Button type="button" variant="secondary" onClick={handleBack}>
                  <ArrowLeft className="w-4 h-4" /> Back
                </Button>
                <Button type="submit" loading={submitMutation.isPending}>
                  Submit Request
                </Button>
              </div>
            </div>
          )}
        </form>
      </Card>
    </div>
  );
}

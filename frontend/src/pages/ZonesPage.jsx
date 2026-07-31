import { useState, useEffect } from 'react';
import { Search, Server, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../api/client';
import Card from '../components/shared/Card';
import Input from '../components/shared/Input';
import Button from '../components/shared/Button';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import Alert from '../components/shared/Alert';

export default function ZonesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [zones, setZones] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [totalZones, setTotalZones] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 100;

  useEffect(() => {
    loadZones();
  }, [page]);

  const loadZones = async () => {
    setIsLoading(true);
    try {
      const result = await api.getZones(page * pageSize, pageSize);
      setZones(result.zones || []);
      setTotalZones(result.total || 0);
      setHasMore(result.has_more || false);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredZones = zones.filter((zone) =>
    zone.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return <LoadingSpinner text="Loading DNS zones..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Failed to load zones">
        {error.message || 'Could not fetch DNS zones from Azure. Please check your permissions.'}
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">DNS Zones</h1>
          <p className="mt-1 text-gray-600">
            {totalZones.toLocaleString()} zone(s) total • Showing page {page + 1} of {Math.ceil(totalZones / pageSize)}
          </p>
        </div>
      </div>

      <Card>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Search zones..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </Card>

      {filteredZones.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Server className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">
              {searchQuery ? 'No zones match your search.' : 'No DNS zones found.'}
            </p>
          </div>
        </Card>
      ) : (
        <div className="overflow-hidden border border-gray-200 rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Zone Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource Group
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Record Sets
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredZones.map((zone) => (
                <tr key={zone.name} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{zone.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {zone.resource_group}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                      {zone.zone_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                    {zone.record_set_count}
                  </td>
                </tr>
              ))}
            </tbody>

        {/* Pagination */}
        <div className="mt-4 flex items-center justify-between border-t pt-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || isLoading}
          >
            <ChevronLeft className="w-4 h-4" /> Previous
          </Button>
          
          <span className="text-sm text-gray-600">
            {page * pageSize + 1}-{Math.min((page + 1) * pageSize, totalZones)} of {totalZones.toLocaleString()}
          </span>
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(p => p + 1)}
            disabled={!hasMore || isLoading}
          >
            Next <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
          </table>
        </div>
      )}
    </div>
  );
}

import { useLocation, Link } from 'react-router-dom';
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';
import Alert from '../components/shared/Alert';

export default function ConfirmationPage() {
  const location = useLocation();
  const { results = [], zone = '', action = '' } = location.state || {};

  if (!results.length) {
    return (
      <div className="max-w-2xl mx-auto">
        <Alert variant="warning" title="No results to display">
          No submission data found. Please submit a request first.
        </Alert>
        <div className="mt-4 flex justify-center">
          <Link to="/request">
            <Button>Create New Request</Button>
          </Link>
        </div>
      </div>
    );
  }

  const failedResults = results.filter((r) => r.error);
  const successResults = results.filter((r) => !r.error);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4">
          {failedResults.length > 0 ? (
            <XCircle className="w-16 h-16 text-red-500" />
          ) : (
            <CheckCircle className="w-16 h-16 text-green-500" />
          )}
        </div>
        <h1 className="text-3xl font-bold text-gray-900">
          {failedResults.length > 0
            ? `${failedResults.length} of ${results.length} Change(s) Failed`
            : `${successResults.length} Change(s) Applied Successfully`}
        </h1>
        <p className="mt-2 text-gray-600">
          Zone: <span className="font-semibold">{zone}</span> • Action:{' '}
          <span className="font-semibold capitalize">{action}</span>
        </p>
      </div>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Results Summary</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Label</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">TTL</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((result, index) => (
                <tr key={index} className={result.error ? 'bg-red-50' : ''}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded">
                      {result.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{result.label}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                    {result.value}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{result.ttl}s</td>
                  <td className="px-4 py-3">
                    {result.error ? (
                      <div className="flex items-center gap-2 text-red-600">
                        <XCircle className="w-4 h-4" />
                        <span className="text-xs">{result.error}</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-xs">Success</span>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="flex justify-center gap-4">
        <Link to="/request">
          <Button>
            New Request <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
        <Link to="/zones">
          <Button variant="secondary">Back to Zones</Button>
        </Link>
      </div>
    </div>
  );
}

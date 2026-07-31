import { Link } from 'react-router-dom';
import { CheckCircle, ArrowRight } from 'lucide-react';
import Card from '../components/shared/Card';
import Button from '../components/shared/Button';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200">
        <div className="text-center py-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Welcome to Unilever DNS Self Service Portal
          </h1>
          <p className="text-lg text-gray-700 mb-4">
            This portal is to perform create/update/delete records for domains managed by Cloud BAU team.
          </p>
          <p className="text-sm text-gray-600">
            For any support, reach <a href="mailto:UL_cloudops@hcltech.com" className="text-primary-600 hover:underline font-medium">UL_cloudops@hcltech.com</a>
          </p>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="hover:shadow-md transition-shadow">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-primary-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-primary-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-1">Service Active</h3>
              <p className="text-sm text-gray-600">
                The DNS portal is running and ready to process your requests.
              </p>
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-1">Phase 2 Active</h3>
              <p className="text-sm text-gray-600">
                Strong foundation for A, AAAA, CNAME, TXT records with enhanced error handling.
              </p>
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-1">Phase 1 Complete</h3>
              <p className="text-sm text-gray-600">
                Modern React UI with fast, responsive interface.
              </p>
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="text-xl font-semibold mb-4">Quick Start</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
              1
            </span>
            <p className="text-sm text-gray-700">
              Browse available DNS zones in your Azure subscription
            </p>
            <Link to="/zones" className="ml-auto">
              <Button size="sm" variant="outline">
                View Zones <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
              2
            </span>
            <p className="text-sm text-gray-700">
              Submit a DNS change request (Create, Modify, or Delete records)
            </p>
            <Link to="/request" className="ml-auto">
              <Button size="sm">
                New Request <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
              3
            </span>
            <p className="text-sm text-gray-700">
              Changes are validated and executed automatically
            </p>
          </div>
        </div>
      </Card>

      <Card className="bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">Phase 1: Modern UI ✅</h3>
        <ul className="text-sm text-blue-800 space-y-1 ml-4 list-disc">
          <li>Fast, responsive React interface</li>
          <li>Real-time validation and error prevention</li>
          <li>Clean, professional design</li>
          <li>Optimized performance with caching</li>
        </ul>
        <p className="mt-3 text-xs text-blue-700">
          Coming next: Phase 2 (Core Logic), Phase 3 (PostgreSQL + SSO), Phase 4 (Audit Logging), Phase 5 (Testing & Production)
        </p>
      </Card>
    </div>
  );
}

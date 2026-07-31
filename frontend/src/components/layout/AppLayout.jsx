import { Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import Header from './Header';
import Sidebar from './Sidebar';
import { api } from '../../api/client';

export default function AppLayout() {
  // Fetch app config from backend
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.health,
    staleTime: 300000, // 5 minutes
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        appName={config?.app_name || 'Azure DNS Portal'}
        version={config?.version || '2.0.0'}
        environment={config?.environment || 'production'}
      />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-4 md:p-6 overflow-x-hidden">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

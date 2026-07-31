import { Globe } from 'lucide-react';

export default function Header({ appName = 'Azure DNS Portal', version = '2.0.0', environment = 'production' }) {
  return (
    <header className="bg-primary-700 text-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Globe className="w-8 h-8" />
          <div>
            <h1 className="text-xl font-bold">{appName}</h1>
            <p className="text-xs text-primary-100">Self-Service DNS Management</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-primary-800 rounded-full text-xs font-medium">
            v{version}
          </span>
          <span className="px-3 py-1 bg-white/10 rounded-full text-xs font-medium">
            {environment}
          </span>
        </div>
      </div>
    </header>
  );
}

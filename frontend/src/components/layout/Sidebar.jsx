import { NavLink } from 'react-router-dom';
import { Home, Globe, FileText } from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
  { name: 'Dashboard', path: '/', icon: Home },
  { name: 'DNS Zones', path: '/zones', icon: Globe },
  { name: 'New Request', path: '/request', icon: FileText },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-73px)]">
      <nav className="p-4 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={clsx('w-5 h-5', isActive ? 'text-primary-600' : 'text-gray-500')} />
                  {item.name}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

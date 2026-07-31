# Frontend - Azure DNS Portal

Modern React-based UI for the Azure DNS Self-Service Portal.

## Technology Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server (fast HMR)
- **TanStack Query** - Server state management and caching
- **React Router** - Client-side routing
- **React Hook Form** - Form state management
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Icon library
- **React Hot Toast** - Toast notifications

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server with hot reload:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`. API calls are automatically proxied to the backend at `http://localhost:8000`.

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/                  # API client functions
│   │   └── client.js         # Fetch wrapper with error handling
│   ├── components/
│   │   ├── layout/           # Layout components (Header, Sidebar, AppLayout)
│   │   ├── shared/           # Reusable UI components (Button, Input, Card, etc.)
│   │   └── request/          # DNS request form components
│   │       ├── StepIndicator.jsx
│   │       ├── CreateRecordForm.jsx
│   │       ├── ModifyRecordForm.jsx
│   │       └── DeleteRecordForm.jsx
│   ├── pages/                # Page components (routes)
│   │   ├── DashboardPage.jsx
│   │   ├── ZonesPage.jsx
│   │   ├── RequestPage.jsx
│   │   └── ConfirmationPage.jsx
│   ├── App.jsx               # Main app with routing
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles (Tailwind)
├── index.html                # HTML template
├── package.json              # Dependencies and scripts
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind CSS configuration
└── postcss.config.js         # PostCSS configuration
```

## Features

### Performance Optimizations

- **Code Splitting**: Automatic route-based splitting via React.lazy()
- **Tree Shaking**: Vite removes unused code
- **Asset Optimization**: Images and fonts optimized automatically
- **Gzip Compression**: Enabled in production build
- **Browser Caching**: Immutable assets with content hashes

### Data Caching

TanStack Query provides:
- Automatic background refetching
- Cache invalidation after mutations
- Optimistic updates
- Retry logic for failed requests
- 60-second stale time for zones

### Validation

- **Client-side**: Real-time validation with inline errors
- **Server-side**: Backend validates all requests
- **Type-specific**: IPv4/IPv6/FQDN format validation
- **Duplicate detection**: Prevents conflicting records
- **SPF warnings**: Alerts for potential mail delivery issues

### User Experience

- **Wizard Interface**: 3-step process for DNS requests
- **Loading States**: Skeleton loaders and spinners
- **Error Handling**: Toast notifications and inline errors
- **Search & Filter**: Instant client-side search for zones/records
- **Responsive Design**: Mobile-friendly with Tailwind breakpoints

## Configuration

Environment variables (create `.env` file):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Azure DNS Portal
VITE_APP_VERSION=2.0.0
```

## Troubleshooting

### API Connection Issues

If the frontend can't connect to the backend:

1. Verify backend is running: `curl http://localhost:8000/api/health`
2. Check proxy configuration in `vite.config.js`
3. Ensure CORS is enabled in backend `app/main.py`

### Build Errors

If `npm run build` fails:

1. Delete `node_modules/` and `package-lock.json`
2. Run `npm install` again
3. Check Node.js version: `node --version` (should be 18+)

### Slow Performance

If the app feels slow:

1. Check Network tab in DevTools for slow API calls
2. Verify backend caching is working
3. Clear browser cache and reload

## Next Steps (Future Phases)

- **Phase 2**: Enhanced DNS execution logic
- **Phase 3**: PostgreSQL integration + SSO authentication
- **Phase 4**: Audit logging and request history
- **Phase 5**: Unit tests and E2E tests

## License

Internal use only - HCL Technologies Limited

import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import ZonesPage from './pages/ZonesPage'
import RequestPage from './pages/RequestPage'
import ConfirmationPage from './pages/ConfirmationPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="zones" element={<ZonesPage />} />
        <Route path="request" element={<RequestPage />} />
        <Route path="confirmation" element={<ConfirmationPage />} />
      </Route>
    </Routes>
  )
}

export default App

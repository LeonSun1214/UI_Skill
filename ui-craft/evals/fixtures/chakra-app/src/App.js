import { ChakraProvider } from '@chakra-ui/react';
import { Navigate, Route, Routes } from 'react-router-dom';
import AdminLayout from './layouts/admin';
import AuthLayout from './layouts/auth';
import theme from './theme/theme';

export default function App() {
  return (
    <ChakraProvider theme={theme}>
      <Routes>
        <Route path="auth/*" element={<AuthLayout />} />
        <Route path="admin/*" element={<AdminLayout />} />
        <Route path="/" element={<Navigate to="/admin/default" replace />} />
      </Routes>
    </ChakraProvider>
  );
}

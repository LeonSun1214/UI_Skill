import { Flex } from '@chakra-ui/react';
import { Route, Routes } from 'react-router-dom';
import routes from '../../routes';

export default function AuthLayout() {
  return (
    <Flex minH="100vh" align="center" justify="center">
      <Routes>{routes.filter((r) => r.layout === '/auth').map((r) => <Route key={r.path} path={r.path} element={r.component} />)}</Routes>
    </Flex>
  );
}

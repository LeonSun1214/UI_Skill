import { Box, Flex, Text, useColorModeValue } from '@chakra-ui/react';
import { Route, Routes } from 'react-router-dom';
import routes from '../../routes';

export default function AdminLayout() {
  const bg = useColorModeValue('secondaryGray.300', 'navy.900');
  const getRoutes = (list) => list.filter((r) => r.layout === '/admin').map((r) => <Route key={r.path} path={r.path} element={r.component} />);
  return (
    <Flex bg={bg} minH="100vh">
      <Box as="nav" w="260px" p={6}><Text fontWeight="700">Harbor</Text></Box>
      <Box as="main" flex="1" p={8}><Routes>{getRoutes(routes)}</Routes></Box>
    </Flex>
  );
}

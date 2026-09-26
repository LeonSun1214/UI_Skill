import { Box, Table, Tbody, Td, Th, Thead, Tr, useColorModeValue } from '@chakra-ui/react';

export default function Orders() {
  const card = useColorModeValue('white', 'navy.800');
  return (
    <Box bg={card} p={5} borderRadius="20px">
      <Table>
        <Thead><Tr><Th>Order</Th><Th>Status</Th></Tr></Thead>
        <Tbody><Tr><Td>#1042</Td><Td>Packed</Td></Tr></Tbody>
      </Table>
    </Box>
  );
}

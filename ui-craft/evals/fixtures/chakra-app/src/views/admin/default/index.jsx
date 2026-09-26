import { Box, Button, Flex, Heading, SimpleGrid, Text, useColorModeValue } from '@chakra-ui/react';

export default function Dashboard() {
  const card = useColorModeValue('white', 'navy.800');
  const muted = useColorModeValue('secondaryGray.600', 'secondaryGray.400');
  return (
    <Box>
      <Heading size="lg" mb={6}>Dashboard</Heading>
      <SimpleGrid columns={{ base: 1, md: 3 }} gap={5}>
        {['Open', 'Late', 'Shipped'].map((k) => (
          <Flex key={k} direction="column" bg={card} p={5} borderRadius="20px">
            <Text color={muted} fontSize="sm">{k}</Text>
            <Text fontSize="2xl" fontWeight="700">12</Text>
          </Flex>
        ))}
      </SimpleGrid>
      <Button colorScheme="brand" mt={6}>New order</Button>
    </Box>
  );
}

import { Button, FormControl, FormLabel, Heading, Input, Stack } from '@chakra-ui/react';

export default function SignIn() {
  return (
    <Stack as="form" spacing={4} w="360px">
      <Heading size="lg">Sign in</Heading>
      <FormControl><FormLabel>Email</FormLabel><Input type="email" name="email" /></FormControl>
      <FormControl><FormLabel>Password</FormLabel><Input type="password" name="password" /></FormControl>
      <Button colorScheme="brand" type="submit">Sign in</Button>
    </Stack>
  );
}

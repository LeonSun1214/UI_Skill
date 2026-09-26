import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

export default function SignInPage() {
  return (
    <Box component="form" sx={{ display: 'grid', gap: 2, maxWidth: 360, mx: 'auto', mt: 10 }}>
      <Typography variant="h4" component="h1">Sign in</Typography>
      <TextField label="Email" name="email" type="email" />
      <TextField label="Password" name="password" type="password" />
      <Button variant="contained" type="submit">Sign in</Button>
    </Box>
  );
}

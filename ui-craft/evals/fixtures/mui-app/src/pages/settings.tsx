import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

export default function SettingsPage() {
  return (
    <Card sx={{ p: 3, maxWidth: 560 }}>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>Settings</Typography>
      <Box component="form" sx={{ display: 'grid', gap: 2 }}>
        <TextField label="Display name" name="name" />
        <TextField label="Email" name="email" type="email" />
        <Button variant="contained" type="submit">Save</Button>
      </Box>
    </Card>
  );
}

import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

const STATS = [
  { label: 'Open orders', value: 42 },
  { label: 'Late', value: 3 },
  { label: 'Shipped today', value: 17 },
];

export function OverviewView() {
  return (
    <Grid container spacing={3}>
      {STATS.map((s) => (
        <Grid key={s.label} size={{ xs: 12, md: 4 }}>
          <Card>
            <CardHeader title={s.label} />
            <CardContent>
              <Typography variant="h3" sx={{ color: 'primary.main' }}>{s.value}</Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>this week</Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
      <Grid size={12}>
        <Card>
          <CardHeader title="Late orders" />
          <Table>
            <TableHead>
              <TableRow><TableCell>Order</TableCell><TableCell>Due</TableCell></TableRow>
            </TableHead>
            <TableBody>
              <TableRow><TableCell>#1042</TableCell><TableCell>Tue</TableCell></TableRow>
            </TableBody>
          </Table>
        </Card>
      </Grid>
    </Grid>
  );
}

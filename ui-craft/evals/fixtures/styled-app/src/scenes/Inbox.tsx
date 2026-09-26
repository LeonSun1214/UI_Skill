import styled from 'styled-components';
import Button from '~/components/Button';
import Card from '~/components/Card';

const Muted = styled.p`
  color: ${({ theme }) => theme.textSecondary};
`;

export default function Inbox() {
  return (
    <Card>
      <h1>Inbox</h1>
      <Muted>Three new messages.</Muted>
      <Button type="button">Compose</Button>
    </Card>
  );
}

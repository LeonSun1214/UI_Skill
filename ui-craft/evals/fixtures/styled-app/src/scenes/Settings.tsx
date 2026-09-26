import styled from 'styled-components';
import Button from '~/components/Button';
import Card from '~/components/Card';

const Field = styled.input`
  min-height: 44px;
  border: 1px solid ${({ theme }) => theme.divider};
  border-radius: 8px;
  color: ${({ theme }) => theme.text};
`;

export default function Settings() {
  return (
    <Card as="form">
      <h1>Settings</h1>
      <label htmlFor="name">Name</label>
      <Field id="name" name="name" />
      <Button type="submit">Save</Button>
    </Card>
  );
}

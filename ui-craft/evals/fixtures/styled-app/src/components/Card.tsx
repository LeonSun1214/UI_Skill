import styled from 'styled-components';

const Card = styled.section`
  padding: 24px;
  border: 1px solid ${({ theme }) => theme.divider};
  border-radius: 12px;
  background: ${({ theme }) => theme.backgroundSecondary};
  color: ${({ theme }) => theme.text};
`;

export default Card;

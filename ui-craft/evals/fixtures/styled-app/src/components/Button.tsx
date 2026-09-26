import styled from 'styled-components';

const Button = styled.button`
  min-height: 44px;
  padding: 0 16px;
  border: 0;
  border-radius: 8px;
  background: ${({ theme }) => theme.accent};
  color: #fff;
`;

export default Button;

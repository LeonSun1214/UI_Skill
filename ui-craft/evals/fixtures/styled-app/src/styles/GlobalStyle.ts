import { createGlobalStyle } from 'styled-components';

export default createGlobalStyle`
  body {
    margin: 0;
    font-family: system-ui, sans-serif;
    background: ${({ theme }) => theme.background};
    color: ${({ theme }) => theme.text};
  }
`;

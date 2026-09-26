import { theme } from 'antd';

export const antd = (memo: any) => {
  const dark = localStorage.getItem('harbor-dark') === '1';
  memo.theme = { ...memo.theme, algorithm: dark ? theme.darkAlgorithm : theme.defaultAlgorithm };
  return memo;
};

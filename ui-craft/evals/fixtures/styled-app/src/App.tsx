import { ThemeProvider } from 'styled-components';
import { Route, Switch } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import GlobalStyle from '~/styles/GlobalStyle';
import { useThemeChoice } from '~/stores/ui';
import { darkTheme, lightTheme } from '~/styles/theme';

const Inbox = lazy(() => import('~/scenes/Inbox'));
const Settings = lazy(() => import('~/scenes/Settings'));

export default function App() {
  const choice = useThemeChoice();
  return (
    <ThemeProvider theme={choice === 'dark' ? darkTheme : lightTheme}>
      <GlobalStyle />
      <Suspense fallback={null}>
        <Switch>
          <Route exact path="/" component={Inbox} />
          <Route path="/settings" component={Settings} />
        </Switch>
      </Suspense>
    </ThemeProvider>
  );
}

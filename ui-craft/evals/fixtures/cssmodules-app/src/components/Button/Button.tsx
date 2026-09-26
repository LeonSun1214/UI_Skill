import type { ReactNode } from 'react';
import styles from './Button.module.css';

export default function Button({ children }: { children: ReactNode }) {
  return <button type="button" className={styles.button}>{children}</button>;
}

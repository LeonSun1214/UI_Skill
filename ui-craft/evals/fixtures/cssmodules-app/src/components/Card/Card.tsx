import type { ReactNode } from 'react';
import styles from './Card.module.css';

export default function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className={styles.card}>
      <h2 className={styles.title}>{title}</h2>
      {children}
    </section>
  );
}

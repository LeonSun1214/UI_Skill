import styles from './Header.module.css';

export default function Header() {
  return (
    <header className={styles.header}>
      <span className={styles.brand}>Pantry</span>
    </header>
  );
}

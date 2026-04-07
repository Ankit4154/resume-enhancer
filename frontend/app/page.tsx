'use client';

import ResumeAnalyzerApp from './components/ui/ResumeAnalyzerApp';
import styles from './styles/Home.module.css';

export default function Home() {
  return (
    <main className={styles.App}>
      <div className={styles.container}>
        <div className={styles.content}>
          <div className={styles.centeredContent}>
            {}
            <ResumeAnalyzerApp />
          </div>
        </div>
      </div>
    </main>
  )
}
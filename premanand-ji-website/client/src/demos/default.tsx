/* src/demos/default.tsx */
import React from 'react';
import { LoopingWords } from '@/components/ui/looping-words-with-gsap';

const DemoPage: React.FC = () => {
  const words = ["राधा"];

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <LoopingWords words={words} />
    </div>
  );
};

export default DemoPage;

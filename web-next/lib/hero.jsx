'use client';
import { useEffect, useState } from 'react';

const GREEK = 'αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ';

export function ScrambleWord() {
  // Greek noise resolves left to right into RECEIPT, holds, scrambles again.
  const FINAL = 'receipt';
  const [text, setText] = useState(FINAL);
  useEffect(() => {
    let frame = 0;
    let live = true;
    const pick = () => GREEK[Math.floor(Math.random() * GREEK.length)];
    const id = setInterval(() => {
      if (!live) return;
      frame += 1;
      if (frame < 8) {
        // full scramble
        setText(Array.from({ length: FINAL.length },
          () => pick()).join(''));
      } else if (frame < 8 + FINAL.length * 3) {
        // resolve one letter every 3 frames
        const n = Math.min(FINAL.length,
          Math.floor((frame - 8) / 3) + 1);
        setText(FINAL.slice(0, n) + Array.from(
          { length: FINAL.length - n }, () => pick()).join(''));
      } else if (frame < 8 + FINAL.length * 3 + 40) {
        setText(FINAL);
      } else {
        frame = 0;
      }
    }, 60);
    return () => { live = false; clearInterval(id); };
  }, []);
  return <span className="swapword">{text}</span>;
}

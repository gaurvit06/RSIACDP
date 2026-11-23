import { createContext, useLayoutEffect, useRef, useState, type ReactNode } from 'react';

export const DialogClosing = createContext(false);

// Keep the last dialog contents for the exit animation. Inert removes them
// from keyboard, pointer and accessibility navigation as soon as it closes.
export function DialogTransition({ children }: { children: ReactNode }) {
  const lastOpen = useRef<ReactNode>(null);
  const generation = useRef(0);
  const lastKey = useRef(0);
  const [retained, setRetained] = useState(false);
  const open = Boolean(children);

  useLayoutEffect(() => {
    if (open) {
      lastOpen.current = children;
      lastKey.current = generation.current;
      setRetained(true);
    }
  }, [children, open]);

  useLayoutEffect(() => {
    if (open || !retained) return;
    generation.current += 1;
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const finish = () => { lastOpen.current = null; setRetained(false); };
    if (preference.matches) { finish(); return; }
    // Also releases the contents when CSS animations are unavailable or cancelled.
    const timer = window.setTimeout(finish, 155);
    preference.addEventListener('change', finish);
    return () => { window.clearTimeout(timer); preference.removeEventListener('change', finish); };
  }, [open, retained]);

  if (!open && !retained) return null;
  return <DialogClosing.Provider value={!open}>
    <div key={open ? generation.current : lastKey.current} className="dialog-transition" data-closing={!open} inert={!open}>
      {open ? children : lastOpen.current}
    </div>
  </DialogClosing.Provider>;
}

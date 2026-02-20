import { PropsWithChildren } from 'react';

export function PageHeader({ children }: PropsWithChildren) {
  return (
    <header className="flex justify-between items-center bg-text-title-invert py-1.5 px-5">
      {children}
    </header>
  );
}

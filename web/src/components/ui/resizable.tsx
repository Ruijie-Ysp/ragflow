'use client';

import { cn } from '@/lib/utils';
import { GripVertical } from 'lucide-react';
import * as React from 'react';

interface ResizablePanelGroupProps {
  direction?: 'horizontal' | 'vertical';
  className?: string;
  children: React.ReactNode;
}

interface ResizablePanelProps {
  defaultSize?: number;
  minSize?: number;
  maxSize?: number;
  className?: string;
  children: React.ReactNode;
}

interface ResizableHandleProps {
  className?: string;
  withHandle?: boolean;
}

interface PanelContext {
  sizes: number[];
  setSizes: React.Dispatch<React.SetStateAction<number[]>>;
  direction: 'horizontal' | 'vertical';
}

const PanelGroupContext = React.createContext<PanelContext | null>(null);

export function ResizablePanelGroup({
  direction = 'horizontal',
  className,
  children,
}: ResizablePanelGroupProps) {
  const childArray = React.Children.toArray(children);
  const panelCount = childArray.filter(
    (child) =>
      React.isValidElement(child) &&
      (child.type as any)?.displayName === 'ResizablePanel',
  ).length;

  const [sizes, setSizes] = React.useState<number[]>(() => {
    const defaultSizes: number[] = [];
    React.Children.forEach(children, (child) => {
      if (
        React.isValidElement(child) &&
        (child.type as any)?.displayName === 'ResizablePanel'
      ) {
        defaultSizes.push(child.props.defaultSize || 100 / panelCount);
      }
    });
    return defaultSizes;
  });

  return (
    <PanelGroupContext.Provider value={{ sizes, setSizes, direction }}>
      <div
        className={cn(
          'flex h-full w-full',
          direction === 'vertical' ? 'flex-col' : 'flex-row',
          className,
        )}
        data-panel-group=""
        data-panel-group-direction={direction}
      >
        {children}
      </div>
    </PanelGroupContext.Provider>
  );
}

export function ResizablePanel({
  defaultSize,
  minSize = 10,
  maxSize = 90,
  className,
  children,
}: ResizablePanelProps) {
  const context = React.useContext(PanelGroupContext);
  const panelRef = React.useRef<HTMLDivElement>(null);
  const [index, setIndex] = React.useState(-1);

  React.useEffect(() => {
    if (panelRef.current) {
      const parent = panelRef.current.parentElement;
      if (parent) {
        const panels = Array.from(parent.querySelectorAll('[data-panel]'));
        setIndex(panels.indexOf(panelRef.current));
      }
    }
  }, []);

  const size = context?.sizes[index] ?? defaultSize ?? 33.33;

  return (
    <div
      ref={panelRef}
      data-panel=""
      data-panel-size={size}
      className={cn('overflow-hidden', className)}
      style={{
        flex: `${size} 1 0`,
        minWidth:
          context?.direction === 'horizontal' ? `${minSize}%` : undefined,
        maxWidth:
          context?.direction === 'horizontal' ? `${maxSize}%` : undefined,
        minHeight:
          context?.direction === 'vertical' ? `${minSize}%` : undefined,
        maxHeight:
          context?.direction === 'vertical' ? `${maxSize}%` : undefined,
      }}
    >
      {children}
    </div>
  );
}
ResizablePanel.displayName = 'ResizablePanel';

export function ResizableHandle({
  className,
  withHandle = true,
}: ResizableHandleProps) {
  const context = React.useContext(PanelGroupContext);
  const [isDragging, setIsDragging] = React.useState(false);
  const handleRef = React.useRef<HTMLDivElement>(null);
  const [handleIndex, setHandleIndex] = React.useState(-1);

  React.useEffect(() => {
    if (handleRef.current) {
      const parent = handleRef.current.parentElement;
      if (parent) {
        const handles = Array.from(
          parent.querySelectorAll('[data-panel-resize-handle]'),
        );
        setHandleIndex(handles.indexOf(handleRef.current));
      }
    }
  }, []);

  const handleMouseDown = React.useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);

      const startX = e.clientX;
      const startY = e.clientY;
      const parent = handleRef.current?.parentElement;
      if (!parent || !context) return;

      const parentRect = parent.getBoundingClientRect();
      const startSizes = [...context.sizes];

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const deltaX = moveEvent.clientX - startX;
        const deltaY = moveEvent.clientY - startY;
        const delta = context.direction === 'horizontal' ? deltaX : deltaY;
        const totalSize =
          context.direction === 'horizontal'
            ? parentRect.width
            : parentRect.height;
        const deltaPercent = (delta / totalSize) * 100;

        const newSizes = [...startSizes];
        if (handleIndex >= 0 && handleIndex < newSizes.length - 1) {
          newSizes[handleIndex] = Math.max(
            10,
            Math.min(90, startSizes[handleIndex] + deltaPercent),
          );
          newSizes[handleIndex + 1] = Math.max(
            10,
            Math.min(90, startSizes[handleIndex + 1] - deltaPercent),
          );
          context.setSizes(newSizes);
        }
      };

      const handleMouseUp = () => {
        setIsDragging(false);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [context, handleIndex],
  );

  return (
    <div
      ref={handleRef}
      data-panel-resize-handle=""
      className={cn(
        'relative flex items-center justify-center bg-border',
        context?.direction === 'horizontal'
          ? 'w-1 cursor-col-resize'
          : 'h-1 cursor-row-resize',
        isDragging && 'bg-primary',
        'hover:bg-primary/50 transition-colors',
        className,
      )}
      onMouseDown={handleMouseDown}
    >
      {withHandle && (
        <div className="z-10 flex h-4 w-3 items-center justify-center rounded-sm border bg-border">
          <GripVertical className="size-2.5" />
        </div>
      )}
    </div>
  );
}

import { Button } from '@/components/ui/button';
import { Spin } from '@/components/ui/spin';
import { Authorization } from '@/constants/authorization';
import { ILiterature } from '@/interfaces/database/literature';
import literatureService from '@/services/literature-service';
import { getAuthorization } from '@/utils/authorization-util';
import { FileText, ZoomIn, ZoomOut } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PdfHighlighter, PdfLoader } from 'react-pdf-highlighter';

type PdfLoaderProps = React.ComponentProps<typeof PdfLoader> & {
  httpHeaders?: Record<string, string>;
};

const Loader = PdfLoader as React.ComponentType<PdfLoaderProps>;

interface PdfPanelProps {
  literature: ILiterature;
}

// PDF 缩放级别
const SCALE_VALUES = [
  '0.5',
  '0.75',
  '1',
  '1.25',
  '1.5',
  '2',
  'page-width',
  'auto',
];
const SCALE_LABELS: Record<string, string> = {
  '0.5': '50%',
  '0.75': '75%',
  '1': '100%',
  '1.25': '125%',
  '1.5': '150%',
  '2': '200%',
  'page-width': '适应宽度',
  auto: '自动',
};

export function PdfPanel({ literature }: PdfPanelProps) {
  const { t } = useTranslation();
  const [error, setError] = useState<string>('');
  const [scaleIndex, setScaleIndex] = useState(2); // 默认 100%

  const pdfUrl = useMemo(() => {
    return literatureService.getLiteratureFile(literature.id);
  }, [literature.id]);

  const httpHeaders = useMemo(
    () => ({
      [Authorization]: getAuthorization(),
    }),
    [],
  );

  const currentScale = SCALE_VALUES[scaleIndex];
  const currentLabel = SCALE_LABELS[currentScale] || currentScale;

  const handleZoomIn = () =>
    setScaleIndex((i) => Math.min(i + 1, SCALE_VALUES.length - 1));
  const handleZoomOut = () => setScaleIndex((i) => Math.max(i - 1, 0));
  const handleReset = () => setScaleIndex(2); // 重置到 100%

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-red-500" />
          <span className="text-base font-semibold">
            {t('literature.originalDocument')}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomOut}
            disabled={scaleIndex <= 0}
            title={t('common.zoomOut')}
          >
            <ZoomOut className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="text-xs min-w-[60px]"
            title={t('common.reset')}
          >
            {currentLabel}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomIn}
            disabled={scaleIndex >= SCALE_VALUES.length - 1}
            title={t('common.zoomIn')}
          >
            <ZoomIn className="size-4" />
          </Button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-hidden relative bg-muted/20">
        <Loader
          url={pdfUrl}
          httpHeaders={httpHeaders}
          beforeLoad={
            <div className="flex items-center justify-center h-full">
              <Spin size="large" />
            </div>
          }
          workerSrc="/pdfjs-dist/pdf.worker.min.js"
          errorMessage={
            <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground">
              <FileText className="size-12 text-red-400" />
              <span className="text-sm">
                {error || t('literature.pdfLoadError')}
              </span>
            </div>
          }
          onError={(e) => {
            console.warn('PDF load error:', e);
            setError(String(e));
          }}
        >
          {(pdfDocument) => (
            <PdfHighlighter
              key={currentScale}
              pdfDocument={pdfDocument}
              enableAreaSelection={() => false}
              onScrollChange={() => {}}
              scrollRef={() => {}}
              onSelectionFinished={() => null}
              highlightTransform={() => <div></div>}
              highlights={[]}
              pdfScaleValue={currentScale}
            />
          )}
        </Loader>
      </div>
    </div>
  );
}

import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spin } from '@/components/ui/spin';
import { Input } from 'antd';
import { ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ContentViewerProps {
  content: string;
  type: 'markdown' | 'txt';
  isProcessed: boolean;
}

// 每页显示的字符数
const CHARS_PER_PAGE = 5000;

export function ContentViewer({
  content,
  type,
  isProcessed,
}: ContentViewerProps) {
  const { t } = useTranslation();
  const [currentPage, setCurrentPage] = useState(1);

  // 分页逻辑
  const { totalPages, currentContent } = useMemo(() => {
    if (!content) {
      return { totalPages: 0, currentContent: '' };
    }

    // 按段落分割，尽量保持段落完整
    const paragraphs = content.split(/\n\n+/);
    const pageList: string[] = [];
    let currentPageContent = '';

    for (const paragraph of paragraphs) {
      if (
        currentPageContent.length + paragraph.length > CHARS_PER_PAGE &&
        currentPageContent.length > 0
      ) {
        pageList.push(currentPageContent.trim());
        currentPageContent = paragraph;
      } else {
        currentPageContent += (currentPageContent ? '\n\n' : '') + paragraph;
      }
    }

    if (currentPageContent) {
      pageList.push(currentPageContent.trim());
    }

    const safeCurrentPage = Math.min(currentPage, pageList.length);

    return {
      totalPages: pageList.length,
      currentContent: pageList[safeCurrentPage - 1] || '',
    };
  }, [content, currentPage]);

  const handlePrevPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
  };

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1 && value <= totalPages) {
      setCurrentPage(value);
    }
  };

  if (!isProcessed) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-3 bg-muted/10">
        <Spin size="large" />
        <p className="text-sm">{t('literature.waitingForProcess')}</p>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-3 bg-muted/10">
        <FileText className="size-12 opacity-40" />
        <p className="text-sm">{t('literature.noContent')}</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col min-w-0">
      <ScrollArea className="flex-1 min-w-0">
        <div className="p-6 min-w-0 w-full">
          {type === 'markdown' ? (
            <div className="prose prose-sm dark:prose-invert max-w-none prose-table:border prose-table:border-collapse prose-td:border prose-td:p-2 prose-th:border prose-th:p-2 prose-th:bg-muted/50 break-words">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {currentContent}
              </ReactMarkdown>
            </div>
          ) : (
            <pre className="whitespace-pre-wrap text-sm font-mono bg-muted/30 p-4 rounded-lg border leading-relaxed break-words overflow-x-hidden">
              {currentContent}
            </pre>
          )}
        </div>
      </ScrollArea>

      {/* 分页控制 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t bg-muted/30">
          <span className="text-xs text-muted-foreground">
            {t('common.total')} {totalPages} {t('common.pages')}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={handlePrevPage}
              disabled={currentPage <= 1}
            >
              <ChevronLeft className="size-4" />
            </Button>
            <div className="flex items-center gap-1">
              <Input
                value={currentPage}
                onChange={handlePageInputChange}
                className="w-12 h-8 text-center text-sm"
                min={1}
                max={totalPages}
              />
              <span className="text-sm text-muted-foreground">
                / {totalPages}
              </span>
            </div>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={handleNextPage}
              disabled={currentPage >= totalPages}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

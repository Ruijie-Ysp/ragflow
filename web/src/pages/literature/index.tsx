import { PageHeader } from '@/components/page-header';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { Spin } from '@/components/ui/spin';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useFetchAgentResults,
  useFetchLiteratureDetail,
  useLiteratureId,
} from '@/hooks/use-literature-request';
import { LiteratureProcessStatus } from '@/interfaces/database/literature';
import { Routes } from '@/routes';
import { message } from 'antd';
import { Copy, FileText, RefreshCw } from 'lucide-react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'umi';
import { AgentPanel } from './agent-panel';
import { ContentViewer } from './content-viewer';
import { PdfPanel } from './pdf-panel';

export default function Literature() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const literatureId = useLiteratureId();
  const { literature, loading, refetch } = useFetchLiteratureDetail();
  const {
    results,
    loading: resultsLoading,
    refetch: refetchResults,
  } = useFetchAgentResults(literatureId);
  const [activeTab, setActiveTab] = useState<'markdown' | 'txt'>('markdown');

  const handleBack = useCallback(() => {
    navigate(Routes.Literatures);
  }, [navigate]);

  const handleRefresh = useCallback(() => {
    refetch();
    refetchResults();
  }, [refetch, refetchResults]);

  const handleCopyContent = useCallback(() => {
    if (!literature) return;
    const content =
      activeTab === 'markdown'
        ? literature.markdown_content
        : literature.txt_content;
    if (content) {
      navigator.clipboard
        .writeText(content)
        .then(() => {
          message.success(t('common.copySuccess'));
        })
        .catch(() => {
          message.error(t('common.copyFailed'));
        });
    }
  }, [literature, activeTab, t]);

  if (loading && !literature) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spin size="large" />
      </div>
    );
  }

  if (!literature) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <FileText className="size-16 text-muted-foreground" />
        <p className="text-muted-foreground">{t('literature.notFound')}</p>
        <Button onClick={handleBack}>{t('common.back')}</Button>
      </div>
    );
  }

  const isProcessed =
    literature.process_status === LiteratureProcessStatus.Success;

  return (
    <section className="flex h-full flex-col w-full overflow-hidden">
      {/* Header with Breadcrumb */}
      <PageHeader>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink onClick={handleBack} className="cursor-pointer">
                {t('header.literature')}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage className="max-w-xs whitespace-nowrap text-ellipsis overflow-hidden">
                {literature.name}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="size-4 mr-1" />
            {t('common.refresh')}
          </Button>
        </div>
      </PageHeader>

      {/* Main Content */}
      <div className="flex-1 min-h-0 p-4">
        <ResizablePanelGroup
          direction="horizontal"
          className="h-full rounded-lg border"
        >
          {/* Left Panel - PDF Preview (25%) */}
          <ResizablePanel defaultSize={25} minSize={15} maxSize={40}>
            <div className="h-full bg-background">
              <PdfPanel literature={literature} />
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Middle Panel - Agent Processing (45%) */}
          <ResizablePanel defaultSize={45} minSize={25} maxSize={60}>
            <div className="h-full bg-background border-x">
              <AgentPanel
                literature={literature}
                results={results}
                loading={resultsLoading}
              />
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Right Panel - Markdown/TXT Content (30%) */}
          <ResizablePanel defaultSize={30} minSize={20} maxSize={50}>
            <div className="h-full flex flex-col bg-background">
              {/* Toolbar */}
              <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30 shrink-0">
                <span className="text-base font-semibold">
                  {t('literature.parsedContent')}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleCopyContent}
                  title={t('common.copy')}
                >
                  <Copy className="size-4" />
                </Button>
              </div>

              <Tabs
                value={activeTab}
                onValueChange={(v) => setActiveTab(v as 'markdown' | 'txt')}
                className="flex-1 flex flex-col min-h-0"
              >
                <TabsList className="w-full justify-start rounded-none border-b h-10 px-4 bg-transparent shrink-0">
                  <TabsTrigger
                    value="markdown"
                    className="data-[state=active]:bg-background"
                  >
                    Markdown
                  </TabsTrigger>
                  <TabsTrigger
                    value="txt"
                    className="data-[state=active]:bg-background"
                  >
                    TXT
                  </TabsTrigger>
                </TabsList>
                <TabsContent
                  value="markdown"
                  className="flex-1 m-0 overflow-hidden"
                >
                  <ContentViewer
                    content={literature.markdown_content || ''}
                    type="markdown"
                    isProcessed={isProcessed}
                  />
                </TabsContent>
                <TabsContent value="txt" className="flex-1 m-0 overflow-hidden">
                  <ContentViewer
                    content={literature.txt_content || ''}
                    type="txt"
                    isProcessed={isProcessed}
                  />
                </TabsContent>
              </Tabs>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </section>
  );
}

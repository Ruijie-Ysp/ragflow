import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Spin } from '@/components/ui/spin';
import { AgentCategory } from '@/constants/agent';
import { useFetchAgentList } from '@/hooks/use-agent-request';
import {
  useDeleteAgentResult,
  useRunAgent,
} from '@/hooks/use-literature-request';
import {
  AgentResultStatus,
  ILiterature,
  ILiteratureAgentResult,
  LiteratureProcessStatus,
} from '@/interfaces/database/literature';
import { Divider, Popconfirm, Tooltip, message } from 'antd';
import {
  Bot,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  Copy,
  Download,
  FileSpreadsheet,
  FileText,
  FileType,
  Layers,
  Loader2,
  Play,
  Settings2,
  Trash2,
  XCircle,
} from 'lucide-react';
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface AgentPanelProps {
  literature: ILiterature;
  results: ILiteratureAgentResult[];
  loading: boolean;
}

// 输入来源类型
type InputSourceType = 'markdown' | string; // string for "result:{id}"

// 分段大小预设选项
const SEGMENT_SIZE_OPTIONS = [
  { value: 12000, label: '12K', desc: '标准' },
  { value: 30000, label: '30K', desc: '中等' },
  { value: 50000, label: '50K', desc: '大上下文' },
  { value: 100000, label: '100K', desc: '超大上下文' },
  { value: 0, label: '不分段', desc: '一次性处理' },
];

export function AgentPanel({ literature, results, loading }: AgentPanelProps) {
  const { t } = useTranslation();
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [inputSource, setInputSource] = useState<InputSourceType>('markdown');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [maxSegmentChars, setMaxSegmentChars] = useState<number>(12000);
  const { runAgent, loading: runLoading } = useRunAgent();
  const { deleteAgentResult, loading: deleteLoading } = useDeleteAgentResult();
  const { data: agentData } = useFetchAgentList({
    canvas_category: AgentCategory.AgentCanvas,
  });
  const agentList = agentData?.canvas || [];

  const isProcessed =
    literature.process_status === LiteratureProcessStatus.Success;
  const canRunAgent = isProcessed && selectedAgentId && !runLoading;

  // 获取成功的智能体结果列表（可作为入参）
  const successfulResults = useMemo(() => {
    return results.filter(
      (r) => r.status === AgentResultStatus.Success && r.output_content,
    );
  }, [results]);

  // 计算当前选择的输入内容长度
  const inputContentInfo = useMemo(() => {
    let content = '';
    let sourceLabel = '';

    if (inputSource === 'markdown') {
      content = literature.markdown_content || '';
      sourceLabel = t('literature.inputSourceMarkdown');
    } else if (inputSource.startsWith('result:')) {
      const resultId = inputSource.split(':')[1];
      const result = successfulResults.find((r) => r.id === resultId);
      content = result?.output_content || '';
      sourceLabel = result?.agent_title || t('literature.agentResult');
    }

    const totalChars = content.length;
    // 如果 maxSegmentChars 为 0，表示不分段
    const effectiveSegmentSize =
      maxSegmentChars > 0 ? maxSegmentChars : totalChars;
    const segmentCount =
      effectiveSegmentSize > 0
        ? Math.ceil(totalChars / effectiveSegmentSize)
        : 1;
    const needsSegment = segmentCount > 1;

    return { totalChars, segmentCount, needsSegment, sourceLabel };
  }, [
    inputSource,
    literature.markdown_content,
    successfulResults,
    t,
    maxSegmentChars,
  ]);

  const handleRunAgent = async () => {
    if (!selectedAgentId) return;
    const agent = agentList.find((a) => a.id === selectedAgentId);
    // 如果不分段（maxSegmentChars 为 0），传递一个很大的值
    const effectiveMaxSegmentChars =
      maxSegmentChars > 0 ? maxSegmentChars : 999999999;
    await runAgent({
      literatureId: literature.id,
      agentId: selectedAgentId,
      agentTitle: agent?.title || '',
      inputSource: inputSource,
      maxSegmentChars: effectiveMaxSegmentChars,
    });
  };

  const handleDeleteResult = async (resultId: string) => {
    await deleteAgentResult(resultId);
  };

  const handleCopyResult = useCallback(
    (content: string) => {
      navigator.clipboard
        .writeText(content)
        .then(() => {
          message.success(t('common.copySuccess'));
        })
        .catch(() => {
          message.error(t('common.copyFailed'));
        });
    },
    [t],
  );

  // 解析 HTML 表格为二维数组
  const parseHtmlTable = (html: string): string[][] => {
    const rows: string[][] = [];
    const rowMatches = html.match(/<tr[^>]*>([\s\S]*?)<\/tr>/gi) || [];
    for (const row of rowMatches) {
      const cells: string[] = [];
      const cellMatches = row.match(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi) || [];
      for (const cell of cellMatches) {
        const text = cell
          .replace(/<t[dh][^>]*>/i, '')
          .replace(/<\/t[dh]>/i, '')
          .replace(/<[^>]+>/g, '')
          .trim();
        cells.push(text);
      }
      if (cells.length > 0) rows.push(cells);
    }
    return rows;
  };

  // 解析 Markdown 表格为二维数组
  const parseMarkdownTable = (md: string): string[][] => {
    const rows: string[][] = [];
    const lines = md.split('\n');
    for (const line of lines) {
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        // 跳过分隔行 (|---|---|)
        if (/^\|[\s\-:|]+\|$/.test(line.trim())) continue;
        const cells = line
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim());
        if (cells.length > 0) rows.push(cells);
      }
    }
    return rows;
  };

  // 将 Markdown 转换为 HTML
  const markdownToHtml = (md: string): string => {
    let html = md;
    // 标题
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    // 粗体和斜体
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // 处理 Markdown 表格
    const tableRegex = /(\|.+\|[\r\n]+\|[-:\s|]+\|[\r\n]+(\|.+\|[\r\n]*)+)/g;
    html = html.replace(tableRegex, (match) => {
      const rows = parseMarkdownTable(match);
      if (rows.length === 0) return match;
      let table =
        '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;">';
      rows.forEach((row, i) => {
        table += '<tr>';
        row.forEach((cell) => {
          table += i === 0 ? `<th>${cell}</th>` : `<td>${cell}</td>`;
        });
        table += '</tr>';
      });
      table += '</table>';
      return table;
    });
    // 换行
    html = html.replace(/\n/g, '<br>');
    return html;
  };

  // 下载文件的通用函数
  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 导出为 Markdown
  const handleExportMarkdown = useCallback(
    (content: string, agentTitle: string) => {
      const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
      downloadFile(blob, `${agentTitle || 'result'}_${Date.now()}.md`);
      message.success(t('literature.exportSuccess'));
    },
    [t],
  );

  // 导出为 TXT（去除 HTML 标签）
  const handleExportTxt = useCallback(
    (content: string, agentTitle: string) => {
      const plainText = content.replace(/<[^>]+>/g, '').replace(/\|/g, '\t');
      const blob = new Blob([plainText], { type: 'text/plain;charset=utf-8' });
      downloadFile(blob, `${agentTitle || 'result'}_${Date.now()}.txt`);
      message.success(t('literature.exportSuccess'));
    },
    [t],
  );

  // 导出为 Word (HTML格式)
  const handleExportWord = useCallback(
    (content: string, agentTitle: string) => {
      // 检测内容类型并转换
      let bodyContent = content;
      if (!content.includes('<table') && !content.includes('<h1')) {
        // 如果是 Markdown，转换为 HTML
        bodyContent = markdownToHtml(content);
      }
      const htmlContent = `
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${agentTitle || 'Result'}</title>
<style>
  body { font-family: "Microsoft YaHei", Arial, sans-serif; padding: 20px; line-height: 1.6; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th, td { border: 1px solid #333; padding: 8px; text-align: left; }
  th { background-color: #f0f0f0; font-weight: bold; }
  h1, h2, h3, h4 { margin: 15px 0 10px 0; }
</style>
</head>
<body>
${bodyContent}
</body>
</html>`;
      const blob = new Blob([htmlContent], {
        type: 'application/msword;charset=utf-8',
      });
      downloadFile(blob, `${agentTitle || 'result'}_${Date.now()}.doc`);
      message.success(t('literature.exportSuccess'));
    },
    [t],
  );

  // 导出为 Excel (CSV格式，正确解析表格)
  const handleExportExcel = useCallback(
    (content: string, agentTitle: string) => {
      let rows: string[][] = [];

      // 优先解析 HTML 表格
      if (content.includes('<table')) {
        rows = parseHtmlTable(content);
      }
      // 其次解析 Markdown 表格
      else if (content.includes('|')) {
        rows = parseMarkdownTable(content);
      }

      // 如果解析到表格数据
      if (rows.length > 0) {
        const csvContent = rows
          .map((row) =>
            row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(','),
          )
          .join('\n');
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csvContent], {
          type: 'text/csv;charset=utf-8',
        });
        downloadFile(blob, `${agentTitle || 'result'}_${Date.now()}.csv`);
      } else {
        // 没有表格，按行导出
        const lines = content.split('\n').filter((l) => l.trim());
        const csvContent = lines
          .map((line) => `"${line.replace(/"/g, '""')}"`)
          .join('\n');
        const BOM = '\uFEFF';
        const blob = new Blob([BOM + csvContent], {
          type: 'text/csv;charset=utf-8',
        });
        downloadFile(blob, `${agentTitle || 'result'}_${Date.now()}.csv`);
      }
      message.success(t('literature.exportSuccess'));
    },
    [t],
  );

  // 导出为 PDF (使用打印功能)
  const handleExportPdf = useCallback(
    (content: string, agentTitle: string) => {
      let bodyContent = content;
      if (!content.includes('<table') && !content.includes('<h1')) {
        bodyContent = markdownToHtml(content);
      }
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${agentTitle || 'Result'}</title>
<style>
  body { font-family: "Microsoft YaHei", Arial, sans-serif; padding: 20px; line-height: 1.6; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th, td { border: 1px solid #333; padding: 8px; text-align: left; }
  th { background-color: #f0f0f0; font-weight: bold; }
  h1, h2, h3, h4 { margin: 15px 0 10px 0; }
  @media print { body { padding: 0; } }
</style>
</head>
<body>
<h1>${agentTitle || 'Result'}</h1>
${bodyContent}
</body>
</html>`);
        printWindow.document.close();
        printWindow.print();
      }
      message.info(t('literature.exportPdfHint'));
    },
    [t],
  );

  // 导出为 JSON
  const handleExportJson = useCallback(
    (result: ILiteratureAgentResult) => {
      const jsonData = {
        id: result.id,
        literature_id: result.literature_id,
        agent_id: result.agent_id,
        agent_title: result.agent_title,
        version: result.version,
        output_content: result.output_content,
        status: result.status,
        process_duration: result.process_duration,
        create_date: result.create_date,
        update_date: result.update_date,
      };
      const jsonString = JSON.stringify(jsonData, null, 2);
      const blob = new Blob([jsonString], {
        type: 'application/json;charset=utf-8',
      });
      downloadFile(
        blob,
        `${result.agent_title || 'result'}_${Date.now()}.json`,
      );
      message.success(t('literature.exportSuccess'));
    },
    [t],
  );

  const getResultStatusBadge = (status: string) => {
    switch (status) {
      case AgentResultStatus.Processing:
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Loader2 className="size-3 animate-spin" />
            {t('literature.agentProcessing')}
          </Badge>
        );
      case AgentResultStatus.Success:
        return (
          <CheckCircle
            className="size-4 text-green-500"
            title={t('literature.agentSuccess')}
          />
        );
      case AgentResultStatus.Failed:
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <XCircle className="size-3" />
            {t('literature.agentFailed')}
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30 shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="size-4 text-blue-500" />
          <span className="text-base font-semibold">
            {t('literature.agentProcessing')}
          </span>
        </div>
      </div>

      {/* Agent Selection */}
      <div className="px-4 py-3 shrink-0 space-y-3">
        {!isProcessed ? (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400">
            <Clock className="size-4" />
            <span className="text-sm">{t('literature.processFirst')}</span>
          </div>
        ) : (
          <>
            {/* 输入来源选择 */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                {t('literature.inputSource')}
              </label>
              <Select value={inputSource} onValueChange={setInputSource}>
                <SelectTrigger className="h-9">
                  <SelectValue
                    placeholder={t('literature.selectInputSource')}
                  />
                </SelectTrigger>
                <SelectContent className="max-w-[400px]">
                  <SelectItem value="markdown">
                    <div className="flex items-center gap-2">
                      <FileText className="size-4 text-blue-500 shrink-0" />
                      <span>{t('literature.inputSourceMarkdown')}</span>
                      <span className="text-xs text-muted-foreground ml-auto">
                        {(
                          literature.markdown_content?.length || 0
                        ).toLocaleString()}{' '}
                        {t('literature.chars')}
                      </span>
                    </div>
                  </SelectItem>
                  {successfulResults.length > 0 && (
                    <>
                      <div className="px-2 py-1.5 text-xs text-muted-foreground border-t mt-1 pt-2">
                        {t('literature.agentResultsAsInput')} (
                        {successfulResults.length})
                      </div>
                      {successfulResults.map((result) => (
                        <SelectItem
                          key={result.id}
                          value={`result:${result.id}`}
                        >
                          <div className="flex flex-col gap-0.5 py-0.5 min-w-0">
                            <div className="flex items-center gap-2">
                              <Bot className="size-4 text-green-500 shrink-0" />
                              <span className="font-medium truncate">
                                {result.agent_title ||
                                  t('literature.agentResult')}
                              </span>
                              <Badge
                                variant="outline"
                                className="shrink-0 text-xs"
                              >
                                v{result.version}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground ml-6">
                              <span>
                                {result.create_date?.slice(5, 16) || ''}
                              </span>
                              <span>·</span>
                              <span>
                                {(
                                  result.output_content?.length || 0
                                ).toLocaleString()}{' '}
                                {t('literature.chars')}
                              </span>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </>
                  )}
                </SelectContent>
              </Select>

              {/* 内容长度和分段提示 */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-muted-foreground">
                  {t('literature.contentLength')}:{' '}
                  {inputContentInfo.totalChars.toLocaleString()}{' '}
                  {t('literature.chars')}
                </span>
                {inputContentInfo.needsSegment && (
                  <Tooltip title={t('literature.segmentHint')}>
                    <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                      <Layers className="size-3" />
                      <span>
                        {t('literature.willSegment', {
                          count: inputContentInfo.segmentCount,
                        })}
                      </span>
                    </div>
                  </Tooltip>
                )}
              </div>
            </div>

            {/* 智能体选择和运行 */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                {t('literature.selectAgent')}
              </label>
              <div className="flex items-center gap-2">
                <Select
                  value={selectedAgentId}
                  onValueChange={setSelectedAgentId}
                >
                  <SelectTrigger className="h-9 flex-1">
                    <SelectValue
                      placeholder={t('literature.selectAgentPlaceholder')}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {agentList.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        <div className="flex items-center gap-2">
                          <Bot className="size-4 text-muted-foreground" />
                          {agent.title}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleRunAgent}
                  disabled={!canRunAgent}
                  className="h-9 px-4"
                  variant={canRunAgent ? 'default' : 'secondary'}
                >
                  {runLoading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Play className="size-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* 高级选项 */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {showAdvanced ? (
                  <ChevronDown className="size-3" />
                ) : (
                  <ChevronRight className="size-3" />
                )}
                <Settings2 className="size-3" />
                <span>{t('literature.advancedOptions')}</span>
              </button>

              {showAdvanced && (
                <div className="pl-4 space-y-2 border-l-2 border-muted">
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">
                      {t('literature.segmentSize')}
                    </label>
                    <div className="flex flex-wrap gap-1">
                      {SEGMENT_SIZE_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => setMaxSegmentChars(option.value)}
                          className={`px-2 py-1 text-xs rounded-md border transition-colors ${
                            maxSegmentChars === option.value
                              ? 'bg-primary text-primary-foreground border-primary'
                              : 'bg-background hover:bg-muted border-input'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {maxSegmentChars === 0
                        ? t('literature.noSegmentDesc')
                        : t('literature.segmentSizeDesc', {
                            size: maxSegmentChars.toLocaleString(),
                          })}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <Divider className="my-0" />

      {/* Results Section */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 shrink-0">
          <span className="text-sm font-medium text-muted-foreground">
            {t('literature.agentResults')}
          </span>
          <Badge variant="outline">{results.length}</Badge>
        </div>

        <ScrollArea className="flex-1 min-h-0 px-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Spin size="large" />
            </div>
          ) : results.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Bot className="size-10 mb-2 opacity-40" />
              <span className="text-sm">{t('literature.noAgentResults')}</span>
            </div>
          ) : (
            <div className="space-y-2 pb-4">
              {results.map((result) => (
                <Card key={result.id} className="overflow-hidden">
                  <CardHeader className="py-2 px-3 bg-muted/30">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium flex items-center gap-2 flex-1 min-w-0">
                        <Bot className="size-4 text-blue-500 shrink-0" />
                        <span className="truncate">
                          {result.agent_title || t('literature.unknownAgent')}
                        </span>
                        <span className="text-xs text-muted-foreground font-normal shrink-0">
                          v{result.version}
                        </span>
                      </CardTitle>
                      <div className="flex items-center gap-1 shrink-0 ml-2">
                        {getResultStatusBadge(result.status)}
                        {result.status === AgentResultStatus.Success &&
                          result.output_content && (
                            <>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="size-7 text-muted-foreground hover:text-blue-500"
                                onClick={() =>
                                  handleCopyResult(result.output_content!)
                                }
                                title={t('common.copy')}
                              >
                                <Copy className="size-4" />
                              </Button>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="size-7 text-muted-foreground hover:text-green-500"
                                    title={t('literature.export')}
                                  >
                                    <Download className="size-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleExportMarkdown(
                                        result.output_content!,
                                        result.agent_title,
                                      )
                                    }
                                  >
                                    <FileText className="size-4 mr-2" />
                                    Markdown (.md)
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleExportTxt(
                                        result.output_content!,
                                        result.agent_title,
                                      )
                                    }
                                  >
                                    <FileType className="size-4 mr-2" />
                                    {t('literature.exportTxt')} (.txt)
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleExportWord(
                                        result.output_content!,
                                        result.agent_title,
                                      )
                                    }
                                  >
                                    <FileText className="size-4 mr-2" />
                                    Word (.doc)
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleExportExcel(
                                        result.output_content!,
                                        result.agent_title,
                                      )
                                    }
                                  >
                                    <FileSpreadsheet className="size-4 mr-2" />
                                    Excel (.csv)
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() =>
                                      handleExportPdf(
                                        result.output_content!,
                                        result.agent_title,
                                      )
                                    }
                                  >
                                    <FileText className="size-4 mr-2" />
                                    PDF
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => handleExportJson(result)}
                                  >
                                    <FileText className="size-4 mr-2" />
                                    JSON (.json)
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </>
                          )}
                        <Popconfirm
                          title={t('literature.deleteResultConfirm')}
                          onConfirm={() => handleDeleteResult(result.id)}
                          okText={t('common.yes')}
                          cancelText={t('common.no')}
                        >
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7 text-muted-foreground hover:text-red-500"
                            disabled={deleteLoading}
                            title={t('common.delete')}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </Popconfirm>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-3">
                    {result.status === AgentResultStatus.Success &&
                      result.output_content && (
                        <div className="text-sm bg-muted/30 p-2 rounded-lg border max-h-64 overflow-auto">
                          <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
                            {result.output_content}
                          </pre>
                        </div>
                      )}
                    {result.status === AgentResultStatus.Failed &&
                      result.error_message && (
                        <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                          {result.error_message}
                        </div>
                      )}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2">
                      <Clock className="size-3" />
                      {result.create_date}
                      {result.process_duration > 0 && (
                        <span className="ml-2 px-1.5 py-0.5 bg-muted rounded text-[10px]">
                          {result.process_duration.toFixed(2)}s
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}

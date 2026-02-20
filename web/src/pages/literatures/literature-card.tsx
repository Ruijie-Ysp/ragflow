import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useCancelProcess,
  useDeleteLiterature,
  useProcessLiterature,
} from '@/hooks/use-literature-request';
import {
  ILiterature,
  LiteratureProcessStatus,
} from '@/interfaces/database/literature';
import { Routes } from '@/routes';
import { formatBytes } from '@/utils/file-util';
import {
  Bot,
  CheckCircle,
  Clock,
  FileText,
  Loader2,
  Play,
  Square,
  Trash2,
  XCircle,
} from 'lucide-react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'umi';

// 支持的解析方法
const PARSE_METHODS = [
  { value: 'MinerU', label: 'MinerU', description: '适合复杂版面PDF' },
  { value: 'DeepDOC', label: 'DeepDOC', description: '内置深度学习解析' },
  { value: 'PlainText', label: 'PlainText', description: '纯文本提取' },
  { value: 'Table', label: 'Table', description: '表格优化解析' },
];

interface LiteratureCardProps {
  literature: ILiterature;
}

export function LiteratureCard({ literature }: LiteratureCardProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { processLiterature, loading: processLoading } = useProcessLiterature();
  const { deleteLiterature, loading: deleteLoading } = useDeleteLiterature();
  const { cancelProcess, loading: cancelLoading } = useCancelProcess();
  const [selectedParseMethod, setSelectedParseMethod] = useState<string>(
    literature.parse_method || 'MinerU',
  );

  const getStatusBadge = useCallback(() => {
    switch (literature.process_status) {
      case LiteratureProcessStatus.Pending:
        return (
          <Badge
            variant="secondary"
            className="flex items-center gap-1 whitespace-nowrap"
          >
            <Clock className="size-3" />
            {t('literature.statusPending')}
          </Badge>
        );
      case LiteratureProcessStatus.Processing:
        return (
          <Badge
            variant="default"
            className="flex items-center gap-1 bg-blue-500 whitespace-nowrap"
          >
            <Loader2 className="size-3 animate-spin" />
            {t('literature.statusProcessing')}
          </Badge>
        );
      case LiteratureProcessStatus.Success:
        return (
          <Badge
            variant="default"
            className="flex items-center gap-1 bg-green-500 whitespace-nowrap"
          >
            <CheckCircle className="size-3" />
            {t('literature.statusSuccess')}
          </Badge>
        );
      case LiteratureProcessStatus.Failed:
        return (
          <Badge
            variant="destructive"
            className="flex items-center gap-1 whitespace-nowrap"
          >
            <XCircle className="size-3" />
            {t('literature.statusFailed')}
          </Badge>
        );
      default:
        return null;
    }
  }, [literature.process_status, t]);

  const handleProcess = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await processLiterature({
      literatureId: literature.id,
      parseMethod: selectedParseMethod,
    });
  };

  const handleParseMethodChange = (value: string) => {
    setSelectedParseMethod(value);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await deleteLiterature(literature.id);
  };

  const handleCancel = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await cancelProcess(literature.id);
  };

  const handleCardClick = () => {
    if (literature.process_status === LiteratureProcessStatus.Success) {
      navigate(`${Routes.Literature}/${literature.id}`);
    }
  };

  const canProcess =
    literature.process_status === LiteratureProcessStatus.Pending ||
    literature.process_status === LiteratureProcessStatus.Failed;
  const isProcessing =
    literature.process_status === LiteratureProcessStatus.Processing;

  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-shadow ${
        literature.process_status === LiteratureProcessStatus.Success
          ? ''
          : 'opacity-80'
      }`}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <FileText className="size-5 text-red-500 shrink-0" />
          <CardTitle
            className="text-sm font-medium truncate flex-1 min-w-0"
            title={literature.name}
          >
            {literature.name}
          </CardTitle>
          <div className="shrink-0 flex items-center gap-1">
            {literature.running_agent_count &&
              literature.running_agent_count > 0 && (
                <Badge
                  variant="outline"
                  className="flex items-center gap-1 whitespace-nowrap border-orange-400 text-orange-600 bg-orange-50"
                >
                  <Bot className="size-3 animate-pulse" />
                  <span className="text-xs">
                    {literature.running_agent_count}
                  </span>
                </Badge>
              )}
            {getStatusBadge()}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-2">
        <div className="text-xs text-muted-foreground space-y-1">
          <div>
            {t('literature.size')}: {formatBytes(literature.size)}
          </div>
          <div>
            {t('literature.createTime')}: {literature.create_date}
          </div>
          {literature.process_duration > 0 && (
            <div>
              {t('literature.processDuration')}:{' '}
              {literature.process_duration.toFixed(2)}s
            </div>
          )}
          {literature.parse_method &&
            literature.process_status === LiteratureProcessStatus.Success && (
              <div>
                {t('literature.parseMethod')}: {literature.parse_method}
              </div>
            )}
          {literature.process_message &&
            literature.process_status === LiteratureProcessStatus.Failed && (
              <div
                className="text-red-500 truncate"
                title={literature.process_message}
              >
                {literature.process_message}
              </div>
            )}
        </div>
      </CardContent>
      <CardFooter className="pt-2 flex-col gap-2">
        {canProcess && (
          <div className="w-full flex items-center gap-2">
            <Select
              value={selectedParseMethod}
              onValueChange={handleParseMethodChange}
            >
              <SelectTrigger
                className="h-8 flex-1 text-xs"
                onClick={(e) => e.stopPropagation()}
              >
                <SelectValue placeholder={t('literature.selectParseMethod')} />
              </SelectTrigger>
              <SelectContent onClick={(e) => e.stopPropagation()}>
                {PARSE_METHODS.map((method) => (
                  <SelectItem key={method.value} value={method.value}>
                    <div className="flex flex-col">
                      <span>{method.label}</span>
                      <span className="text-xs text-muted-foreground">
                        {method.description}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        <div className="w-full flex items-center gap-2">
          {canProcess && (
            <Button
              size="sm"
              onClick={handleProcess}
              disabled={processLoading || isProcessing}
              className="flex-1"
            >
              {processLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Play className="size-4" />
              )}
              {t('literature.process')}
            </Button>
          )}
          {isProcessing && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancel}
              disabled={cancelLoading}
              className="flex-1"
            >
              {cancelLoading ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Square className="size-4" />
              )}
              {t('literature.cancelProcess')}
            </Button>
          )}
          <Button
            size="sm"
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteLoading}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

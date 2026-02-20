import { CardContainer } from '@/components/card-container';
import ListFilterBar from '@/components/list-filter-bar';
import { Button } from '@/components/ui/button';
import { RAGFlowPagination } from '@/components/ui/ragflow-pagination';
import {
  useFetchLiteratureList,
  useUploadLiterature,
} from '@/hooks/use-literature-request';
import { pick } from 'lodash';
import { FileUp, RefreshCw } from 'lucide-react';
import { useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { LiteratureCard } from './literature-card';

export default function Literatures() {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    list,
    total,
    pagination,
    setPagination,
    handleInputChange,
    searchString,
    refetch,
  } = useFetchLiteratureList();

  const { uploadLiterature, loading: uploadLoading } = useUploadLiterature();

  const handlePageChange = useCallback(
    (page: number, pageSize?: number) => {
      setPagination({ page, pageSize });
    },
    [setPagination],
  );

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadLiterature(file);
      e.target.value = '';
    }
  };

  return (
    <section className="py-4 flex-1 flex flex-col">
      <ListFilterBar
        title={t('literature.title')}
        searchString={searchString}
        onSearchChange={handleInputChange}
        className="px-8"
        icon={'file'}
      >
        <Button variant="outline" onClick={() => refetch()} className="mr-2">
          <RefreshCw className="size-4" />
        </Button>
        <Button onClick={handleUploadClick} disabled={uploadLoading}>
          <FileUp className="size-4 mr-1" />
          {t('literature.upload')}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
        />
      </ListFilterBar>
      <div className="flex-1">
        <CardContainer className="max-h-[calc(100dvh-280px)] overflow-auto px-8">
          {list.map((literature) => (
            <LiteratureCard key={literature.id} literature={literature} />
          ))}
          {list.length === 0 && (
            <div className="col-span-full flex items-center justify-center h-40 text-muted-foreground">
              {t('literature.noData')}
            </div>
          )}
        </CardContainer>
      </div>
      <div className="mt-8 px-8">
        <RAGFlowPagination
          {...pick(pagination, 'current', 'pageSize')}
          total={total}
          onChange={handlePageChange}
        />
      </div>
    </section>
  );
}

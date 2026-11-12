import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { ConfirmDialog } from '../components/requests/ConfirmDialog';
import { CreateRequestForm } from '../components/requests/CreateRequestForm';
import { EditRequestModal } from '../components/requests/EditRequestModal';
import { ExportMenu } from '../components/requests/ExportMenu';
import { RequestDetail } from '../components/requests/RequestDetail';
import { RequestsList } from '../components/requests/RequestsList';
import { UnitToggle } from '../components/UnitToggle';
import { useUnit } from '../hooks/useUnit';
import { api } from '../lib/api';

export function SavedRequests() {
  const [unit, setUnit] = useUnit();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const queryClient = useQueryClient();

  const selectedQuery = useQuery({
    queryKey: ['request', selectedId],
    queryFn: ({ signal }) => api.getRequest(selectedId!, signal),
    enabled: selectedId !== null,
    staleTime: 60_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      setSelectedId(null);
      setConfirmDelete(false);
    },
  });

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 md:px-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-stone-900">Saved Requests</h1>
          <p className="text-sm text-stone-500">
            Capture a date range for any place and keep the daily record.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ExportMenu label="Export all" />
          <UnitToggle unit={unit} onChange={setUnit} />
        </div>
      </header>

      {selectedId === null ? (
        <>
          <CreateRequestForm />
          <RequestsList onOpen={(id) => setSelectedId(id)} />
        </>
      ) : (
        <RequestDetail
          id={selectedId}
          unit={unit}
          onBack={() => setSelectedId(null)}
          onEdit={() => setEditOpen(true)}
          onDelete={() => setConfirmDelete(true)}
        />
      )}

      <EditRequestModal
        open={editOpen}
        request={selectedQuery.data ?? null}
        onClose={() => setEditOpen(false)}
      />

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this request?"
        message="This removes the request and its daily temperature rows. It can't be undone."
        confirmLabel={deleteMutation.isPending ? 'Deleting…' : 'Delete'}
        destructive
        onConfirm={() => {
          if (selectedId !== null) deleteMutation.mutate(selectedId);
        }}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}

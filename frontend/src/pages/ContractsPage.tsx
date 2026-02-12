import { useState } from "react";
import { PlusIcon, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useContracts } from "../hooks/useContracts";
import ContractCard from "../components/ContractCard";
import ContractFormDialog from "../components/ContractFormDialog";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorAlert from "../components/ErrorAlert";
import EmptyState from "../components/EmptyState";
import type { ContractWithDetails } from "../types";

export default function ContractsPage() {
  const { data: contracts, isLoading, error, refetch } = useContracts();
  const [formOpen, setFormOpen] = useState(false);
  const [editContract, setEditContract] = useState<ContractWithDetails | null>(
    null
  );

  const handleEdit = (contract: ContractWithDetails) => {
    setEditContract(contract);
    setFormOpen(true);
  };

  const handleOpenChange = (open: boolean) => {
    setFormOpen(open);
    if (!open) setEditContract(null);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">My Contracts</h2>
          <p className="text-sm text-muted-foreground">
            Manage your DVC contracts and point balances
          </p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <PlusIcon className="size-4" />
          Add Contract
        </Button>
      </div>

      {isLoading && <LoadingSkeleton variant="cards" />}

      {error && (
        <ErrorAlert message={error.message} onRetry={() => refetch()} />
      )}

      {contracts && contracts.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No contracts yet"
          description="Add your first DVC contract to get started."
          action={{ label: "Add Contract", onClick: () => setFormOpen(true) }}
        />
      )}

      {contracts && contracts.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
          {contracts.map((contract) => (
            <ContractCard
              key={contract.id}
              contract={contract}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      <ContractFormDialog
        open={formOpen}
        onOpenChange={handleOpenChange}
        editContract={editContract}
      />
    </div>
  );
}

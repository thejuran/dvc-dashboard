import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="text-center py-12 border rounded-lg bg-muted/30">
      {Icon && (
        <Icon className="size-12 text-muted-foreground mx-auto mb-4" />
      )}
      <p className="font-medium">{title}</p>
      <p className="text-muted-foreground text-sm mt-1">{description}</p>
      {action && (
        <Button
          variant="outline"
          className="mt-4"
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

type Variant = "cards" | "table" | "detail" | "form";

function SkeletonBlock({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-muted rounded-md ${className ?? ""}`} />;
}

function CardsVariant() {
  return (
    <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="rounded-xl border p-6 space-y-4">
          <SkeletonBlock className="h-4 w-2/3" />
          <SkeletonBlock className="h-3 w-1/2" />
          <div className="space-y-2 pt-2">
            <SkeletonBlock className="h-3 w-full" />
            <SkeletonBlock className="h-3 w-4/5" />
            <SkeletonBlock className="h-3 w-3/5" />
          </div>
        </div>
      ))}
    </div>
  );
}

function TableVariant() {
  return (
    <div className="rounded-xl border">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 border-b">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonBlock key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex gap-4 px-4 py-3 border-b last:border-b-0">
          {Array.from({ length: 4 }).map((_, j) => (
            <SkeletonBlock key={j} className="h-3 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

function DetailVariant() {
  return (
    <div className="rounded-xl border p-6 space-y-4 max-w-2xl">
      <SkeletonBlock className="h-5 w-1/3" />
      <SkeletonBlock className="h-3 w-2/3" />
      <div className="space-y-3 pt-4">
        <SkeletonBlock className="h-10 w-full" />
        <SkeletonBlock className="h-10 w-full" />
        <SkeletonBlock className="h-10 w-1/3" />
      </div>
    </div>
  );
}

function FormVariant() {
  return (
    <div className="space-y-6">
      {/* Form inputs area */}
      <div className="rounded-xl border p-6 space-y-4">
        <SkeletonBlock className="h-5 w-1/4" />
        <div className="grid gap-4 sm:grid-cols-2">
          <SkeletonBlock className="h-10 w-full" />
          <SkeletonBlock className="h-10 w-full" />
        </div>
        <SkeletonBlock className="h-9 w-28" />
      </div>
      {/* Results area */}
      <div className="rounded-xl border p-6 space-y-3">
        <SkeletonBlock className="h-4 w-1/3" />
        <SkeletonBlock className="h-3 w-full" />
        <SkeletonBlock className="h-3 w-4/5" />
        <SkeletonBlock className="h-3 w-3/5" />
      </div>
    </div>
  );
}

const variants: Record<Variant, () => React.JSX.Element> = {
  cards: CardsVariant,
  table: TableVariant,
  detail: DetailVariant,
  form: FormVariant,
};

export default function LoadingSkeleton({ variant }: { variant: Variant }) {
  const Component = variants[variant];
  return <Component />;
}

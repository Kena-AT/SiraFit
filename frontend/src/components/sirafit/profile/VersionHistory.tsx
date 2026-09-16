import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { History, RotateCcw, Clock, Loader2 } from "lucide-react";
import {
  getProfileHistory,
  revertProfileToVersion,
  type ProfileVersionSummary,
} from "@/lib/api/profiles";

interface VersionHistoryProps {
  open: boolean;
  onClose: () => void;
  onReverted: () => void; // Called after successful revert so parent can refresh
}

export function VersionHistory({ open, onClose, onReverted }: VersionHistoryProps) {
  const [versions, setVersions] = useState<ProfileVersionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [revertingId, setRevertingId] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    getProfileHistory()
      .then(setVersions)
      .catch((err) => toast.error(`Failed to load history: ${err.message}`))
      .finally(() => setLoading(false));
  }, [open]);

  const handleRevert = async (versionId: string, version: number) => {
    if (
      !confirm(
        `Revert to version ${version}? Your current profile will be saved as a new version first.`,
      )
    ) {
      return;
    }
    setRevertingId(versionId);
    try {
      await revertProfileToVersion(versionId);
      toast.success(`Reverted to version ${version}`);
      onReverted();
      onClose();
    } catch (err: any) {
      toast.error(`Revert failed: ${err.message}`);
    } finally {
      setRevertingId(null);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background rounded-lg shadow-lg w-full max-w-lg max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-muted-foreground" />
            <h2 className="font-semibold">Profile Version History</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin mr-2" />
              Loading history...
            </div>
          ) : versions.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No version history yet. Versions are created automatically when you save your profile.
            </div>
          ) : (
            <div className="space-y-2">
              {versions.map((v) => (
                <div
                  key={v.id}
                  className="flex items-center justify-between p-3 rounded-md border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-mono font-semibold text-foreground">v{v.version}</span>
                      {v.summary && (
                        <span className="text-muted-foreground truncate">{v.summary}</span>
                      )}
                    </div>
                    {v.created_at && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {new Date(v.created_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRevert(v.id, v.version)}
                    disabled={revertingId === v.id}
                    className="ml-3 shrink-0"
                  >
                    {revertingId === v.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RotateCcw className="h-4 w-4 mr-1" />
                    )}
                    Revert
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

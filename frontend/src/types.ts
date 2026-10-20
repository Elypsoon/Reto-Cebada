export type Parcel = {
  id: string; state: string; municipality: string; area: number; observed: number | null;
  estimate: number; production: number; low: number | null; high: number | null;
  points: number[][]; center: number[]; bounds: number[]; videoId: string; videoPath: string;
}
export type Curve = { sensor: string; quality: { observations: number; usable: number } | null;
  points: { date: string; value: number | null; hasObservation: boolean }[] }
export type Metrics = { mae: number; rmse: number; r2: number }
export type Model = {
  id: string; name: string; version: string; cutoff: string; artifactCutoff: string; sourceCommit: string;
  scope: string; method: string; validationScheme: string; metrics: Metrics; byState: Record<string, Metrics>;
  interval: { nominal: number; coverage: number; available: boolean; limitation: string };
  sources: string[]; explanation: { available?: boolean; interpretation: string };
  oof: { id: string; state: string; observed: number; estimated: number }[];
  curveMethod: { label: string }; sourceHashes: Record<string, string>;
}
export const format = (value: number, digits = 2) => new Intl.NumberFormat('es-MX', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)

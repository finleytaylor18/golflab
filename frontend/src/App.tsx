import { useEffect, useState } from "react";
import "./App.css";
import { ClubSpecForm } from "./components/ClubSpecForm";
import { SwingProfileForm } from "./components/SwingProfileForm";
import { ResultsDisplay } from "./components/ResultsDisplay";
import { getSwingWeight, getMoi, getBalancePoint, ApiError } from "./api/client";
import { DEFAULT_CLUB, DEFAULT_SWING } from "./api/types";
import { useDebouncedValue } from "./api/useDebouncedValue";

function App() {
  const [club, setClub] = useState(DEFAULT_CLUB);
  const [swing, setSwing] = useState(DEFAULT_SWING);

  const debouncedClub = useDebouncedValue(club, 300);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [swingWeight, setSwingWeight] = useState<string | null>(null);
  const [moment, setMoment] = useState<number | null>(null);
  const [moi, setMoi] = useState<number | null>(null);
  const [balancePoint, setBalancePoint] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([getSwingWeight(debouncedClub), getMoi(debouncedClub), getBalancePoint(debouncedClub)])
      .then(([swingWeightResult, moiResult, balancePointResult]) => {
        if (cancelled) return;
        setSwingWeight(swingWeightResult.swing_weight);
        setMoment(swingWeightResult.moment);
        setMoi(moiResult.moi);
        setBalancePoint(balancePointResult.balance_point);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setSwingWeight(null);
        setMoment(null);
        setMoi(null);
        setBalancePoint(null);
        setError(err instanceof ApiError ? err.message : "Could not reach the GolfLab API. Is it running on :8000?");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedClub]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>GolfLab</h1>
        <p>Interactive club design and performance simulation</p>
      </header>

      <main className="layout">
        <ClubSpecForm value={club} onChange={setClub} />
        <SwingProfileForm value={swing} onChange={setSwing} />
        <ResultsDisplay
          loading={loading}
          error={error}
          swingWeight={swingWeight}
          moment={moment}
          moi={moi}
          balancePoint={balancePoint}
        />
      </main>
    </div>
  );
}

export default App;

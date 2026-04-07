"use client";

import React, { useState, useEffect, useRef } from "react";

// --- Types ---
type Patient = {
  patient_id: string;
  age: number;
  gender: string;
  chief_complaint: string;
  vitals?: {
    heart_rate?: number;
    blood_pressure?: string;
    temperature?: number;
    oxygen_saturation?: number;
  };
  wait_steps?: number;
  assigned_esi?: number;
};

type Resource = {
  type: string;
  status: string;
  occupied_by: string | null;
};

type Observation = {
  patients?: Record<string, Patient>;
  resources?: Record<string, Resource>;
  wait_steps?: Record<string, number>;
  [key: string]: any;
};

type EnvironmentState = {
  score?: number;
  queue_order?: string[];
  optimal_queue_order?: string[];
  [key: string]: any;
};

type ActionLogEntry = {
  step: number;
  action_type: string;
  patient_id?: string;
  reward: number;
  done: boolean;
};

const JSONViewer = ({ data }: { data: any }) => {
  const highlightJSON = (json: any) => {
    if (json === undefined) return "";
    const str = JSON.stringify(json, null, 2);
    return str.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let color = "#f3f4f6"; // default white
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            color = "#f3f4f6"; // key
          } else {
            color = "#86efac"; // string: green-300
          }
        } else if (/true|false/.test(match)) {
          color = "#fca5a5"; // boolean: red-300
        } else if (/[0-9]/.test(match)) {
          color = "#fde047"; // number: yellow-300
        }
        return `<span style="color: ${color}">${match}</span>`;
      }
    );
  };

  return (
    <pre
      className="p-4 bg-gray-900 border border-gray-700 rounded text-sm overflow-auto custom-scrollbar h-full font-mono whitespace-pre-wrap break-words"
      dangerouslySetInnerHTML={{ __html: highlightJSON(data) }}
    />
  );
};

export default function Dashboard() {
  // State
  const [taskId, setTaskId] = useState("task_1");
  const [offline, setOffline] = useState(false);
  const [isRunning, setIsRunning] = useState(true);
  
  const [observation, setObservation] = useState<Observation>({});
  const [prevState, setPrevState] = useState<Observation>({});
  const [envState, setEnvState] = useState<EnvironmentState>({});
  
  const [stepCount, setStepCount] = useState(0);
  const [isDone, setIsDone] = useState(false);
  
  const [lastReward, setLastReward] = useState(0);
  const [totalReward, setTotalReward] = useState(0);
  const [currentScore, setCurrentScore] = useState(0);
  
  const [actionLog, setActionLog] = useState<ActionLogEntry[]>([]);
  const [autoStep, setAutoStep] = useState(false);
  
  const [manualAction, setManualAction] = useState('{\n  "task_id": "task_1",\n  "action_type": "classify",\n  "patient_id": "P001",\n  "value": 3\n}');
  const [rawTab, setRawTab] = useState<"observation" | "state">("observation");

  // API Callers
  const checkHealth = async () => {
    try {
      const res = await fetch("/api/state", { method: "GET" }).catch(() => null);
      if (!res || !res.ok) setOffline(true);
      else setOffline(false);
    } catch (e) {
      setOffline(true);
    }
  };

  const fetchScore = async () => {
    try {
      const res = await fetch("/api/score");
      if (res.ok) {
        const data = await res.json();
        setCurrentScore(data.score ?? 0);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchState = async () => {
    try {
      const res = await fetch("/api/state");
      if (res.ok) {
        const data = await res.json();
        setEnvState(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const resetEnv = async () => {
    try {
      setOffline(false);
      const res = await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      });
      if (res.ok) {
        const obs = await res.json();
        setPrevState(observation);
        setObservation(obs);
        setStepCount(0);
        setIsDone(false);
        setLastReward(0);
        setTotalReward(0);
        setCurrentScore(0);
        setActionLog([]);
        fetchState();
      } else {
        setOffline(true);
      }
    } catch (e) {
      setOffline(true);
    }
  };

  const stepEnv = async (actionInput?: any) => {
    let actionPayload;
    if (actionInput) {
      actionPayload = actionInput;
    } else {
      try {
        actionPayload = JSON.parse(manualAction);
      } catch (e) {
        alert("Invalid JSON action");
        return;
      }
    }

    try {
      setOffline(false);
      if (!actionPayload.task_id) actionPayload.task_id = taskId;
      
      const res = await fetch("/api/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(actionPayload),
      });
      if (res.ok) {
        const data = await res.json();
        const { observation: obs, reward, done } = data;
        
        setPrevState(observation);
        setObservation(obs);
        setLastReward(reward);
        setTotalReward((prev) => prev + reward);
        setStepCount((prev) => prev + 1);
        setIsDone(done);
        
        setActionLog((prev) => [
          {
            step: stepCount + 1,
            action_type: actionPayload.action_type || "Unknown",
            patient_id: actionPayload.patient_id || "-",
            reward,
            done,
          },
          ...prev,
        ]);
        
        fetchScore();
        fetchState();
      } else {
        setOffline(true);
      }
    } catch (e) {
      setOffline(true);
    }
  };

  // Polling State every 2 seconds
  useEffect(() => {
    checkHealth();
    // Initially call state
    fetchState();
    
    const interval = setInterval(() => {
      fetchState();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto Step
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoStep && !isDone && !offline) {
      interval = setInterval(() => {
        stepEnv();
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoStep, isDone, offline, manualAction, stepCount, observation]);


  // Helper renderers
  const renderPatientCards = () => {
    const patients = observation?.patients || {};
    return Object.values(patients).map((p: any, i: number) => {
      let esiColor = "border-gray-500";
      if (p.assigned_esi === 1) esiColor = "border-red-500 bg-red-500/10";
      else if (p.assigned_esi === 2) esiColor = "border-orange-500 bg-orange-500/10";
      else if (p.assigned_esi === 3) esiColor = "border-yellow-500 bg-yellow-500/10";
      else if (p.assigned_esi === 4) esiColor = "border-green-500 bg-green-500/10";
      else if (p.assigned_esi === 5) esiColor = "border-gray-500 bg-gray-500/10";

      const hrHighlight = p.vitals?.heart_rate > 120;
      const o2Highlight = p.vitals?.oxygen_saturation < 90;

      return (
        <div key={i} className={`p-3 bg-gray-800 rounded border-l-4 ${esiColor} mb-2`}>
          <div className="flex justify-between font-bold mb-1">
            <span>{p.patient_id} ({p.age}{p.gender ? p.gender[0] : ""})</span>
            <span>ESI: {p.assigned_esi || "N/A"}</span>
          </div>
          <p className="text-xs text-gray-300 mb-2 truncate" title={p.chief_complaint}>
            {p.chief_complaint || "No complaint recorded"}
          </p>
          <div className="grid grid-cols-2 text-xs gap-1">
            <div className={hrHighlight ? "text-red-400 font-bold" : ""}>HR: {p.vitals?.heart_rate ?? "-"}</div>
            <div>BP: {p.vitals?.blood_pressure ?? "-"}</div>
            <div>Temp: {p.vitals?.temperature ?? "-"}</div>
            <div className={o2Highlight ? "text-red-400 font-bold" : ""}>O2: {p.vitals?.oxygen_saturation ?? "-"}</div>
          </div>
          <div className="mt-2 text-xs text-blue-300">Wait Steps: {p.wait_steps ?? 0}</div>
        </div>
      );
    });
  };

  const getDiffKeys = (oldObj: any, newObj: any) => {
    const diffs: Record<string, { old: any; new: any }> = {};
    if (!oldObj || !newObj) return diffs;
    
    // Simplistic diffing at root level
    const allKeys = new Set([...Object.keys(oldObj), ...Object.keys(newObj)]);
    allKeys.forEach((key) => {
      const oVal = JSON.stringify(oldObj[key]);
      const nVal = JSON.stringify(newObj[key]);
      if (oVal !== nVal) {
        diffs[key] = { old: oVal, new: nVal };
      }
    });
    return diffs;
  };

  const diffKeys = getDiffKeys(prevState, observation);

  return (
    <div className="h-screen w-screen bg-gray-950 text-gray-100 flex flex-col font-sans overflow-hidden">
      {offline && (
        <div className="bg-red-600 text-white font-bold p-2 text-center text-sm shadow-md shrink-0 z-50">
          ⚠️ Backend Offline or Unreachable (http://localhost:8000)
        </div>
      )}

      {/* PANEL 1: CONTROL PANEL */}
      <header className="bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between shadow-sm shrink-0">
        <div className="flex items-center space-x-4">
          <h1 className="font-bold text-xl tracking-tight text-white mr-4">Triage Dashboard</h1>
          <select 
            value={taskId} 
            onChange={(e) => setTaskId(e.target.value)}
            className="bg-gray-800 text-white text-sm border border-gray-700 p-2 rounded outline-none w-32"
          >
            <option value="task_1">Task 1</option>
            <option value="task_2">Task 2</option>
            <option value="task_3">Task 3</option>
          </select>
          <button 
            onClick={resetEnv}
            className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Reset
          </button>
          <button 
            onClick={() => stepEnv()}
            disabled={isDone || autoStep}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            Step
          </button>
          <label className="flex items-center space-x-2 text-sm cursor-pointer ml-4">
            <input 
              type="checkbox" 
              checked={autoStep} 
              onChange={(e) => setAutoStep(e.target.checked)} 
              disabled={isDone}
            />
            <span>Auto-Step (2s)</span>
          </label>
        </div>
        <div className="flex items-center space-x-6 text-sm">
          <div className="bg-gray-800 px-3 py-1 rounded border border-gray-700">
            Step: <span className="font-bold text-white">{stepCount}</span>
          </div>
          <div className={`px-3 py-1 rounded font-bold uppercase text-xs border ${isDone ? 'bg-red-500/20 text-red-400 border-red-500/50' : 'bg-green-500/20 text-green-400 border-green-500/50'}`}>
            Episode {isDone ? 'DONE' : 'RUNNING'}
          </div>
        </div>
      </header>

      <main className="flex-1 grid grid-cols-12 gap-4 p-4 min-h-0 overflow-hidden">
        
        {/* LEFT COLUMN */}
        <div className="col-span-3 flex flex-col gap-4 h-full min-h-0 overflow-hidden">
          {/* PANEL 2: RAW STATE VIEW */}
          <div className="bg-gray-800 rounded shadow border border-gray-700 flex flex-col flex-1 min-h-0 overflow-hidden">
            <div className="flex border-b border-gray-700 text-sm">
              <button 
                className={`flex-1 py-2 font-medium ${rawTab === 'observation' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-750'}`}
                onClick={() => setRawTab('observation')}
              >
                Observation
              </button>
              <button 
                className={`flex-1 py-2 font-medium ${rawTab === 'state' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-750'}`}
                onClick={() => setRawTab('state')}
              >
                State
              </button>
            </div>
            <div className="p-2 flex-1 overflow-hidden bg-gray-900">
               <JSONViewer data={rawTab === 'observation' ? observation : envState} />
            </div>
          </div>

          {/* PANEL 6: ACTION LOG */}
          <div className="bg-gray-800 rounded shadow border border-gray-700 h-64 shrink-0 flex flex-col">
            <div className="px-4 py-2 border-b border-gray-700 font-bold text-sm text-gray-300 bg-gray-850">
              Action Log
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2 text-xs">
              {actionLog.map((log, i) => (
                <div key={i} className="flex flex-col bg-gray-900 p-2 rounded border border-gray-700">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-blue-400 text-[10px]">#{log.step}</span>
                    <span className={`px-2 rounded-full font-bold text-[10px] ${log.reward > 0 ? 'bg-green-500/20 text-green-400' : log.reward < 0 ? 'bg-red-500/20 text-red-400' : 'bg-gray-600 text-gray-300'}`}>
                      {log.reward > 0 ? '+' : ''}{log.reward.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-300">Type:</span> <span className="text-white">{log.action_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-300">Target:</span> <span className="text-purple-300">{log.patient_id}</span>
                  </div>
                </div>
              ))}
              {actionLog.length === 0 && <div className="text-gray-500 text-center mt-6 italic">No actions yet</div>}
            </div>
          </div>
        </div>

        {/* CENTER COLUMN */}
        <div className="col-span-5 flex flex-col gap-4 h-full min-h-0 overflow-hidden">
          {/* PANEL 3: PATIENT VIEW */}
          <div className="bg-gray-800 rounded shadow border border-gray-700 flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-700 font-bold text-sm text-gray-300 bg-gray-850 flex justify-between shrink-0">
              <span>Patient View</span>
              <span className="text-xs bg-gray-700 px-2 py-0.5 rounded-full">{Object.keys(observation?.patients || {}).length} Total</span>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
              {Object.keys(observation?.patients || {}).length > 0 ? (
                renderPatientCards()
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500 italic text-sm">
                  No patients found in observation.
                </div>
              )}
            </div>
          </div>

          {/* PANEL 7: REWARD & SCORE */}
          <div className="bg-gray-800 rounded shadow border border-gray-700 p-4 h-40 shrink-0 flex flex-col">
            <h3 className="text-sm font-bold text-gray-400 mb-3 uppercase tracking-wider">Performance metrics</h3>
            <div className="grid grid-cols-2 gap-4 flex-1">
              <div className="bg-gray-900 rounded p-3 flex flex-col items-center justify-center border border-gray-750">
                <span className="text-xs text-gray-400 mb-1">Last Reward</span>
                <span className={`text-2xl font-black ${lastReward > 0 ? 'text-green-400' : lastReward < 0 ? 'text-red-400' : 'text-gray-300'}`}>
                  {lastReward > 0 ? '+' : ''}{lastReward.toFixed(2)}
                </span>
                <span className="text-xs text-gray-500 mt-1">Total: {totalReward.toFixed(2)}</span>
              </div>
              <div className="bg-gray-900 rounded p-3 flex flex-col justify-center border border-gray-750">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-xs text-gray-400">Current Score</span>
                  <span className="text-xl font-black text-blue-400">{(currentScore * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 h-2.5 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${Math.min(100, Math.max(0, currentScore * 100))}%` }}></div>
                </div>
                <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                  <span>0.0</span>
                  <span>1.0</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="col-span-4 flex flex-col gap-4 h-full min-h-0 overflow-hidden">
          
          <div className="flex space-x-4 h-64 shrink-0">
            {/* PANEL 4: QUEUE VIEW */}
            <div className="flex-1 bg-gray-800 rounded shadow border border-gray-700 flex flex-col min-h-0 overflow-hidden">
              <div className="px-3 py-2 border-b border-gray-700 font-bold text-xs text-gray-300 bg-gray-850">
                Queue Order
              </div>
              <div className="p-2 flex-1 overflow-y-auto custom-scrollbar text-xs">
                {envState?.queue_order ? (
                  <ol className="list-decimal pl-6 space-y-1">
                    {envState.queue_order.map((id: string, idx: number) => {
                      const optimalOpt = envState?.optimal_queue_order;
                      const isMismatch = optimalOpt && optimalOpt[idx] !== id;
                      return (
                        <li key={idx} className={isMismatch ? "text-orange-400 font-bold bg-orange-900/30 -ml-4 pl-4 rounded" : "text-gray-300"}>
                          <span className="inline-block w-12">{id}</span>
                          {optimalOpt && <span className="ml-2 text-gray-500 font-normal">| opt: {optimalOpt[idx]}</span>}
                        </li>
                      );
                    })}
                  </ol>
                ) : (
                  <div className="text-gray-500 italic text-center mt-4">Queue not available</div>
                )}
              </div>
            </div>

            {/* PANEL 5: RESOURCE VIEW */}
            <div className="flex-1 bg-gray-800 rounded shadow border border-gray-700 flex flex-col min-h-0 overflow-hidden">
              <div className="px-3 py-2 border-b border-gray-700 font-bold text-xs text-gray-300 bg-gray-850 shrink-0">
                Resources
              </div>
              <div className="p-2 flex-1 overflow-y-auto custom-scrollbar space-y-2">
                {observation?.resources ? (
                  Object.entries(observation.resources).map(([id, res]) => (
                    <div key={id} className={`p-2 rounded border text-xs ${res.status?.toLowerCase() === 'free' ? 'border-green-500/50 bg-green-900/10' : 'border-red-500/50 bg-red-900/10'}`}>
                      <div className="font-bold text-white mb-0.5">{id}</div>
                      <div className="text-gray-400">Type: {res.type}</div>
                      <div className={`mt-1 font-medium ${res.status?.toLowerCase() === 'free' ? 'text-green-400' : 'text-red-400'}`}>
                        {res.status} {res.occupied_by ? `> ${res.occupied_by}` : ''}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-gray-500 italic text-center mt-4 text-xs">No resources</div>
                )}
              </div>
            </div>
          </div>

          {/* PANEL 8: DEBUG PANEL */}
          <div className="bg-gray-800 rounded shadow border border-gray-700 flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="px-4 py-2 border-b border-gray-700 font-bold text-sm text-gray-300 bg-gray-850 flex justify-between items-center shrink-0">
              <span>Debug Console</span>
              <div className="text-xs font-normal bg-gray-900 px-2 py-1 rounded border border-gray-700">Max Steps: 30</div>
            </div>
            
            <div className="p-3 flex-1 min-h-0 overflow-hidden flex flex-col space-y-3">
              {/* State Diff */}
              <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
                <div className="text-xs text-gray-400 font-bold mb-1 uppercase tracking-wider shrink-0">State Diff <span className="font-normal normal-case">(Old → New)</span></div>
                <div className="bg-gray-900 border border-gray-700 rounded p-2 flex-1 overflow-y-auto custom-scrollbar text-[11px] font-mono leading-relaxed">
                  {Object.keys(diffKeys).length > 0 ? (
                    Object.entries(diffKeys).map(([key, vals]) => (
                      <div key={key} className="mb-1 border-b border-gray-800 pb-1">
                        <span className="text-white font-bold">{key}</span>: <br/>
                        <span className="text-red-400 line-through mr-1 truncate">{vals.old}</span> → <span className="text-green-400 truncate">{vals.new}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-500 italic h-full flex items-center justify-center">No observation changes yet...</div>
                  )}
                </div>
              </div>

              {/* Manual Action Input */}
              <div className="h-32 flex flex-col shrink-0">
                <div className="text-xs text-gray-400 font-bold mb-1 uppercase tracking-wider">Manual Action Payload JSON</div>
                <textarea 
                  className="w-full flex-1 bg-gray-900 border border-gray-700 rounded p-2 text-xs font-mono text-gray-300 focus:outline-none focus:border-blue-500 custom-scrollbar resize-none"
                  value={manualAction}
                  onChange={(e) => setManualAction(e.target.value)}
                  placeholder="Enter JSON action..."
                />
              </div>
            </div>

          </div>

        </div>
      </main>
    </div>
  );
}

import { useEffect, useState } from "react";
import { fetchAgentStatus, importCapturedJob } from "../lib/api";
import { clearExtensionToken, getExtensionToken, setExtensionToken } from "../lib/auth";
import { CaptureValidationResult } from "../types/job";

export default function Popup() {
  const [status, setStatus] = useState<any>(null);
  const [tokenInput, setTokenInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [captureResult, setCaptureResult] = useState<CaptureValidationResult | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    setLoading(true);
    const token = await getExtensionToken();
    if (token) {
      const currentStatus = await fetchAgentStatus();
      setStatus(currentStatus);
    } else {
      setStatus(null);
    }
    setLoading(false);
  };

  const handleConnect = async () => {
    if (!tokenInput.trim()) return;
    await setExtensionToken(tokenInput.trim());
    await checkStatus();
  };

  const handleDisconnect = async () => {
    await clearExtensionToken();
    setStatus(null);
    setCaptureResult(null);
    setSuccess("");
    setError("");
  };

  const handleCapture = async () => {
    setError("");
    setSuccess("");
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab.id) return;

    chrome.tabs.sendMessage(tab.id, { type: "CAPTURE_ACTIVE_TAB" }, (response) => {
      if (chrome.runtime.lastError) {
        setError("Make sure you are on a supported job page.");
        return;
      }
      if (response?.error) {
        setError(response.error);
      } else if (response?.data) {
        setCaptureResult(response.data);
      }
    });
  };

  const handleImport = async () => {
    if (!captureResult) return;
    setLoading(true);
    setError("");
    try {
      await importCapturedJob(captureResult.data);
      setSuccess("Job successfully imported!");
      setCaptureResult(null);
    } catch (err: any) {
      setError(err.message || "Failed to import job");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 20, minWidth: 300 }}>Loading...</div>;
  }

  if (!status) {
    return (
      <div style={{ padding: 20, minWidth: 300, display: "flex", flexDirection: "column", gap: 10 }}>
        <h2>Connect to SiraFit</h2>
        <p>Enter your extension token from the settings page.</p>
        <input 
          type="text" 
          value={tokenInput} 
          onChange={(e) => setTokenInput(e.target.value)} 
          placeholder="srf_ext_..." 
          style={{ padding: "8px", width: "100%" }}
        />
        <button onClick={handleConnect} style={{ padding: "8px" }}>Connect</button>
      </div>
    );
  }

  return (
    <div style={{ padding: 20, minWidth: 320, display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <strong>SiraFit Connected</strong>
        <button onClick={handleDisconnect}>Disconnect</button>
      </div>
      <div style={{ fontSize: "12px", color: "gray" }}>
        Logged in as: {status.user_email}
      </div>

      <hr style={{ width: "100%", margin: "10px 0" }} />

      {!captureResult && (
        <button 
          onClick={handleCapture}
          style={{ padding: "10px", backgroundColor: "#000", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
        >
          Capture Job
        </button>
      )}

      {error && <div style={{ color: "red", fontSize: "14px" }}>{error}</div>}
      {success && <div style={{ color: "green", fontSize: "14px" }}>{success}</div>}

      {captureResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ fontSize: "14px", fontWeight: "bold" }}>Review Capture</div>
          
          <label style={{ fontSize: "12px" }}>Title</label>
          <input 
            value={captureResult.data.title} 
            onChange={(e) => setCaptureResult({ ...captureResult, data: { ...captureResult.data, title: e.target.value } })}
            style={{ padding: "6px" }}
          />

          <label style={{ fontSize: "12px" }}>Company</label>
          <input 
            value={captureResult.data.company} 
            onChange={(e) => setCaptureResult({ ...captureResult, data: { ...captureResult.data, company: e.target.value } })}
            style={{ padding: "6px" }}
          />

          <label style={{ fontSize: "12px" }}>Location</label>
          <input 
            value={captureResult.data.location} 
            onChange={(e) => setCaptureResult({ ...captureResult, data: { ...captureResult.data, location: e.target.value } })}
            style={{ padding: "6px" }}
          />
          
          {captureResult.warnings.length > 0 && (
            <div style={{ backgroundColor: "#fff3cd", padding: "8px", borderRadius: "4px", fontSize: "12px" }}>
              <strong>Warnings:</strong>
              <ul style={{ margin: 0, paddingLeft: "20px" }}>
                {captureResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
            <button onClick={handleImport} style={{ flex: 1, padding: "8px", backgroundColor: "#000", color: "#fff" }}>
              Import to SiraFit
            </button>
            <button onClick={() => setCaptureResult(null)} style={{ flex: 1, padding: "8px" }}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

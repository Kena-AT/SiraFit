import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { ExtractedJob, CandidateProfile, CaptureResult } from "../shared/types";
import { extractJobFromDOM } from "../content/extractor";
import { autofillApplicationForm } from "../content/autofill";

declare const chrome: any;

export const PopupApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"capture" | "autofill" | "settings">("capture");
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<{ email: string; name?: string } | null>(null);
  const [tokenInput, setTokenInput] = useState<string>("");
  const [apiBaseInput, setApiBaseInput] = useState<string>("http://localhost:8000/api/v1");
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Capture State
  const [extractedJob, setExtractedJob] = useState<ExtractedJob | null>(null);
  const [captureResult, setCaptureResult] = useState<CaptureResult | null>(null);

  // Autofill State
  const [overwriteExisting, setOverwriteExisting] = useState<boolean>(false);
  const [autofillResultText, setAutofillResultText] = useState<string | null>(null);

  useEffect(() => {
    loadState();
  }, []);

  const loadState = () => {
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({ type: "GET_STATE" }, (response: any) => {
        if (response && response.connected) {
          setIsConnected(true);
          setCurrentUser(response.user);
          if (response.token) setTokenInput(response.token);
          if (response.apiBase) setApiBaseInput(response.apiBase);
        } else {
          setIsConnected(false);
          setCurrentUser(null);
        }
      });
    }
  };

  const handleSaveToken = () => {
    setLoading(true);
    setStatusMessage(null);
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage(
        { type: "SAVE_TOKEN", token: tokenInput.trim(), apiBase: apiBaseInput.trim() },
        (response: any) => {
          setLoading(false);
          if (response && response.success) {
            setIsConnected(true);
            setCurrentUser(response.user);
            setStatusMessage({ type: "success", text: "Connected successfully!" });
          } else {
            setStatusMessage({
              type: "error",
              text: response?.error || "Failed to verify token. Check backend connection.",
            });
          }
        }
      );
    } else {
      setLoading(false);
      setStatusMessage({ type: "error", text: "Chrome extension runtime not available" });
    }
  };

  const handleLogout = () => {
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({ type: "LOGOUT" }, () => {
        setIsConnected(false);
        setCurrentUser(null);
        setTokenInput("");
        setStatusMessage({ type: "success", text: "Logged out successfully" });
      });
    }
  };

  const handleExtractFromTab = async () => {
    setLoading(true);
    setStatusMessage(null);
    setCaptureResult(null);

    try {
      if (typeof chrome !== "undefined" && chrome.tabs && chrome.scripting) {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.id) throw new Error("No active tab found");

        const results = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: extractJobFromDOM,
        });

        if (results && results[0] && results[0].result) {
          setExtractedJob(results[0].result);
          setStatusMessage({ type: "success", text: "Job data extracted from page!" });
        } else {
          throw new Error("Could not extract job from this page");
        }
      } else {
        // Mock fallback for browser / development preview
        const job = extractJobFromDOM(document, window.location.href);
        setExtractedJob(job);
        setStatusMessage({ type: "success", text: "Extracted job (preview mode)" });
      }
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to extract job" });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitCapture = () => {
    if (!extractedJob) return;
    setLoading(true);
    setStatusMessage(null);

    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage(
        { type: "SUBMIT_CAPTURE", payload: extractedJob },
        (response: any) => {
          setLoading(false);
          if (response && response.success) {
            setCaptureResult(response.result);
            setStatusMessage({
              type: "success",
              text: response.result.message || "Job captured successfully!",
            });
          } else {
            setStatusMessage({
              type: "error",
              text: response?.error || "Failed to capture job into SiraFit",
            });
          }
        }
      );
    } else {
      setLoading(false);
      setStatusMessage({ type: "error", text: "Extension runtime unavailable" });
    }
  };

  const handleAutofill = async () => {
    setLoading(true);
    setStatusMessage(null);
    setAutofillResultText(null);

    try {
      if (!isConnected) {
        throw new Error("Connect your SiraFit account first in Settings");
      }

      // Fetch profile from background
      const profileResponse: any = await new Promise((resolve) => {
        chrome.runtime.sendMessage({ type: "GET_PROFILE" }, resolve);
      });

      if (!profileResponse || !profileResponse.success) {
        throw new Error(profileResponse?.error || "Could not load candidate profile");
      }

      const profile: CandidateProfile = profileResponse.profile;

      if (typeof chrome !== "undefined" && chrome.tabs && chrome.scripting) {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.id) throw new Error("No active tab found");

        const results = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: autofillApplicationForm,
          args: [document, profile, overwriteExisting],
        });

        const res = results?.[0]?.result;
        if (res) {
          const summary = `Filled ${res.filled_count} fields (${res.fields_filled.join(", ")}). Skipped ${res.skipped_count}.`;
          setAutofillResultText(summary);
          setStatusMessage({ type: "success", text: summary });
        }
      }
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Autofill failed" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="popup-container">
      {/* Header */}
      <div className="header">
        <div className="brand">
          <div className="logo-badge">S</div>
          <span className="brand-name">SiraFit</span>
        </div>
        <div className="status-badge">
          <span className={`status-dot ${isConnected ? "connected" : ""}`}></span>
          <span>{isConnected ? currentUser?.email?.split("@")[0] || "Connected" : "Disconnected"}</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === "capture" ? "active" : ""}`}
          onClick={() => setActiveTab("capture")}
        >
          Capture Job
        </button>
        <button
          className={`tab-btn ${activeTab === "autofill" ? "active" : ""}`}
          onClick={() => setActiveTab("autofill")}
        >
          Autofill Form
        </button>
        <button
          className={`tab-btn ${activeTab === "settings" ? "active" : ""}`}
          onClick={() => setActiveTab("settings")}
        >
          Settings
        </button>
      </div>

      {/* Toast Feedback */}
      {statusMessage && (
        <div className={`toast toast-${statusMessage.type}`}>
          {statusMessage.text}
        </div>
      )}

      {/* TAB 1: CAPTURE */}
      {activeTab === "capture" && (
        <div className="card">
          <span className="card-title">1-Click Job Capture</span>
          <p style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
            Extract and save this listing directly into your SiraFit pipeline.
          </p>

          <button
            className="btn btn-secondary"
            onClick={handleExtractFromTab}
            disabled={loading}
          >
            {loading ? "Scanning page..." : "Scan Active Page"}
          </button>

          {extractedJob && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "6px" }}>
              <div className="field-group">
                <label className="field-label">Job Title</label>
                <input
                  type="text"
                  className="input-text"
                  value={extractedJob.title}
                  onChange={(e) => setExtractedJob({ ...extractedJob, title: e.target.value })}
                />
              </div>

              <div className="field-group">
                <label className="field-label">Company</label>
                <input
                  type="text"
                  className="input-text"
                  value={extractedJob.company}
                  onChange={(e) => setExtractedJob({ ...extractedJob, company: e.target.value })}
                />
              </div>

              <div className="field-group">
                <label className="field-label">Location</label>
                <input
                  type="text"
                  className="input-text"
                  value={extractedJob.location || ""}
                  placeholder="Remote / City"
                  onChange={(e) => setExtractedJob({ ...extractedJob, location: e.target.value })}
                />
              </div>

              <div className="confidence-indicator">
                <span>Platform: <strong>{extractedJob.platform}</strong></span>
                <span>Confidence: <strong>{Math.round(extractedJob.confidence * 100)}%</strong></span>
              </div>

              <button
                className="btn btn-primary"
                onClick={handleSubmitCapture}
                disabled={loading || !isConnected}
              >
                {loading ? "Capturing..." : isConnected ? "Save Job to SiraFit" : "Connect Account First"}
              </button>
            </div>
          )}

          {captureResult && (
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Status: <strong>{captureResult.status}</strong> | ID: {captureResult.job_id || captureResult.import_id}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AUTOFILL */}
      {activeTab === "autofill" && (
        <div className="card">
          <span className="card-title">Candidate Autofill</span>
          <p style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
            Autofill application inputs with your verified SiraFit candidate profile.
          </p>

          <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", color: "var(--text-secondary)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={overwriteExisting}
              onChange={(e) => setOverwriteExisting(e.target.checked)}
            />
            Overwrite existing inputs
          </label>

          <button
            className="btn btn-primary"
            onClick={handleAutofill}
            disabled={loading || !isConnected}
          >
            {loading ? "Filling form..." : isConnected ? "Autofill Application Form" : "Connect Account First"}
          </button>

          {autofillResultText && (
            <div style={{ fontSize: "11px", color: "var(--text-secondary)" }}>
              {autofillResultText}
            </div>
          )}

          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "6px" }}>
            * Note: Autofill never auto-submits forms. Always review inputs manually before submitting.
          </div>
        </div>
      )}

      {/* TAB 3: SETTINGS */}
      {activeTab === "settings" && (
        <div className="card">
          <span className="card-title">Extension Settings</span>

          <div className="field-group">
            <label className="field-label">SiraFit Extension Token</label>
            <input
              type="password"
              className="input-text"
              placeholder="srf_ext_..."
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
            />
            <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>
              Generate a token under your SiraFit Profile Settings.
            </span>
          </div>

          <div className="field-group">
            <label className="field-label">API Base URL</label>
            <input
              type="text"
              className="input-text"
              value={apiBaseInput}
              onChange={(e) => setApiBaseInput(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
            <button
              className="btn btn-primary"
              style={{ flex: 1 }}
              onClick={handleSaveToken}
              disabled={loading || !tokenInput}
            >
              {loading ? "Connecting..." : "Connect Extension"}
            </button>

            {isConnected && (
              <button
                className="btn btn-secondary"
                onClick={handleLogout}
              >
                Disconnect
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Mount root if DOM is ready
if (typeof document !== "undefined") {
  const container = document.getElementById("root");
  if (container) {
    const root = createRoot(container);
    root.render(<PopupApp />);
  }
}

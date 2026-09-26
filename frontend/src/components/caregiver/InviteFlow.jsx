import React, { useState, useEffect } from "react";
import { createInvite, acceptInvite, revokeAccess, listLinkedCaregivers } from "../../api/caregiver";

export default function InviteFlow({ defaultPatientId = "patient-101", onNavigateToDashboard }) {
  const [activeTab, setActiveTab] = useState("send"); // 'send' or 'accept'
  
  // Send Invite Form State
  const [patientId, setPatientId] = useState(defaultPatientId);
  const [caregiverEmail, setCaregiverEmail] = useState("");
  const [caregiverName, setCaregiverName] = useState("");
  const [permissions, setPermissions] = useState("read_respond");
  const [expiresInDays, setExpiresInDays] = useState(7);
  const [sendingInvite, setSendingInvite] = useState(false);
  const [inviteResult, setInviteResult] = useState(null);
  const [sendError, setSendError] = useState(null);

  // Existing Links State
  const [existingLinks, setExistingLinks] = useState([]);
  const [loadingLinks, setLoadingLinks] = useState(false);

  // Accept Form State
  const [acceptToken, setAcceptToken] = useState("");
  const [acceptName, setAcceptName] = useState("");
  const [accepting, setAccepting] = useState(false);
  const [acceptResult, setAcceptResult] = useState(null);
  const [acceptError, setAcceptError] = useState(null);

  // Auto-detect token in URL if present
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const tokenFromUrl = urlParams.get("token");
      if (tokenFromUrl) {
        setAcceptToken(tokenFromUrl);
        setActiveTab("accept");
      }
    }
  }, []);

  const loadExistingLinks = async () => {
    if (!patientId) return;
    try {
      setLoadingLinks(true);
      const data = await listLinkedCaregivers(patientId);
      setExistingLinks(data || []);
    } catch (err) {
      console.error("Failed to load existing links:", err);
    } finally {
      setLoadingLinks(false);
    }
  };

  useEffect(() => {
    loadExistingLinks();
  }, [patientId]);

  const handleSendInvite = async (e) => {
    e.preventDefault();
    if (!caregiverEmail) return;

    try {
      setSendingInvite(true);
      setSendError(null);
      setInviteResult(null);

      const result = await createInvite({
        patient_id: patientId,
        caregiver_email: caregiverEmail,
        caregiver_name: caregiverName || undefined,
        permissions,
        expires_in_days: expiresInDays,
      });

      setInviteResult(result);
      setCaregiverEmail("");
      setCaregiverName("");
      loadExistingLinks();
    } catch (err) {
      setSendError(err.message || "Failed to generate invitation");
    } finally {
      setSendingInvite(false);
    }
  };

  const handleAcceptInvite = async (e) => {
    e.preventDefault();
    if (!acceptToken) return;

    try {
      setAccepting(true);
      setAcceptError(null);
      setAcceptResult(null);

      const result = await acceptInvite({
        invite_token: acceptToken.trim(),
        caregiver_name: acceptName || undefined,
      });

      setAcceptResult(result);
    } catch (err) {
      setAcceptError(err.message || "Failed to accept invitation");
    } finally {
      setAccepting(false);
    }
  };

  const handleRevoke = async (linkId) => {
    if (!window.confirm("Are you sure you want to revoke this caregiver's access?")) return;
    try {
      await revokeAccess(linkId);
      loadExistingLinks();
    } catch (err) {
      alert("Error revoking access: " + err.message);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Invite link copied to clipboard!");
  };

  return (
    <div className="invite-flow-container">
      <div className="flow-tabs-header">
        <button
          className={`tab-btn ${activeTab === "send" ? "tab-active" : ""}`}
          onClick={() => setActiveTab("send")}
        >
          ✉️ Send Caregiver Invite
        </button>
        <button
          className={`tab-btn ${activeTab === "accept" ? "tab-active" : ""}`}
          onClick={() => setActiveTab("accept")}
        >
          🤝 Accept Invitation Link
        </button>
      </div>

      {activeTab === "send" && (
        <div className="tab-pane">
          <div className="card-box">
            <h2 className="pane-title">Link Caregiver to Patient Account</h2>
            <p className="pane-subtitle">
              Issue a secure, time-limited cryptographic token granting role-based access to medication schedules and alerts.
            </p>

            <form onSubmit={handleSendInvite} className="invite-form">
              <div className="form-group-grid">
                <div className="form-field">
                  <label>Patient ID</label>
                  <input
                    type="text"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    required
                    className="form-input"
                  />
                </div>
                <div className="form-field">
                  <label>Caregiver Email</label>
                  <input
                    type="email"
                    placeholder="caregiver@family.org"
                    value={caregiverEmail}
                    onChange={(e) => setCaregiverEmail(e.target.value)}
                    required
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-group-grid">
                <div className="form-field">
                  <label>Caregiver Name (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Priya Patel"
                    value={caregiverName}
                    onChange={(e) => setCaregiverName(e.target.value)}
                    className="form-input"
                  />
                </div>
                <div className="form-field">
                  <label>Role-Based Permissions</label>
                  <select
                    value={permissions}
                    onChange={(e) => setPermissions(e.target.value)}
                    className="form-select"
                  >
                    <option value="read_respond">Read & Respond (View Adherence + Leave Notes + Manage Alerts)</option>
                    <option value="read_only">Read-Only (View Adherence & Timetable Only)</option>
                  </select>
                </div>
              </div>

              <div className="form-field">
                <label>Invite Validity (Days)</label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(e.target.value)}
                  className="form-input-sm"
                />
              </div>

              {sendError && (
                <div className="error-banner">
                  <span>⚠️ {sendError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={sendingInvite}
                className="btn-primary"
              >
                {sendingInvite ? "Generating Secure Token..." : "Generate & Issue Invitation"}
              </button>
            </form>

            {inviteResult && (
              <div className="invite-success-card">
                <div className="success-header">
                  <span className="badge-success">Invite Token Generated</span>
                  <span className="expires-tag">Valid for {expiresInDays} days</span>
                </div>
                <p className="invite-success-text">
                  Share this invitation link with <strong>{inviteResult.caregiver_email}</strong>. 
                  They can accept it to link their caregiver account with <em>{inviteResult.permissions}</em> access.
                </p>
                <div className="token-copy-box">
                  <input
                    type="text"
                    readOnly
                    value={`${window?.location?.origin || ""}${inviteResult.invite_url}`}
                    className="token-input"
                  />
                  <button
                    onClick={() => copyToClipboard(`${window?.location?.origin || ""}${inviteResult.invite_url}`)}
                    className="btn-secondary"
                  >
                    📋 Copy Link
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Linked Caregivers Table */}
          <div className="card-box mt-6">
            <h3 className="section-title">Current & Pending Caregiver Links</h3>
            {loadingLinks ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <span>Loading linked accounts...</span>
              </div>
            ) : existingLinks.length === 0 ? (
              <p className="muted-text">No caregivers currently linked or pending for this patient.</p>
            ) : (
              <div className="table-responsive">
                <table className="styled-table">
                  <thead>
                    <tr>
                      <th>Caregiver</th>
                      <th>Permissions</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {existingLinks.map((link) => (
                      <tr key={link.id}>
                        <td>
                          <strong>{link.caregiver_name || "Invited Caregiver"}</strong>
                          <div className="sub-text">{link.caregiver_email}</div>
                        </td>
                        <td>
                          <span className={`perm-badge ${link.permissions === "read_respond" ? "perm-respond" : "perm-read"}`}>
                            {link.permissions?.replace("_", " & ")}
                          </span>
                        </td>
                        <td>
                          <span className={`status-pill status-${link.status}`}>
                            {link.status}
                          </span>
                        </td>
                        <td>
                          {link.status !== "revoked" ? (
                            <button
                              onClick={() => handleRevoke(link.id)}
                              className="btn-danger-sm"
                            >
                              Revoke
                            </button>
                          ) : (
                            <span className="muted-text">Revoked</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "accept" && (
        <div className="tab-pane">
          <div className="card-box">
            <h2 className="pane-title">Accept Caregiver Invitation</h2>
            <p className="pane-subtitle">
              Verify your invitation token to gain coordinated access to the patient's medication regimen and alerts.
            </p>

            <form onSubmit={handleAcceptInvite} className="accept-form">
              <div className="form-field">
                <label>Invitation Token</label>
                <textarea
                  rows="3"
                  placeholder="Paste your signed invitation token here..."
                  value={acceptToken}
                  onChange={(e) => setAcceptToken(e.target.value)}
                  required
                  className="form-textarea"
                />
              </div>

              <div className="form-field">
                <label>Your Name (Caregiver)</label>
                <input
                  type="text"
                  placeholder="e.g. Priya Patel"
                  value={acceptName}
                  onChange={(e) => setAcceptName(e.target.value)}
                  className="form-input"
                />
              </div>

              {acceptError && (
                <div className="error-banner">
                  <span>⚠️ {acceptError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={accepting || !acceptToken}
                className="btn-primary"
              >
                {accepting ? "Verifying Token..." : "Accept & Link Account"}
              </button>
            </form>

            {acceptResult && (
              <div className="accept-success-card">
                <div className="success-icon">🎉</div>
                <h3>Invitation Accepted Successfully!</h3>
                <p>
                  You are now linked as a caregiver for <strong>{acceptResult.patient_name || acceptResult.patient_id}</strong> with 
                  <strong> {acceptResult.permissions?.replace("_", " & ")}</strong> access level.
                </p>
                <div className="action-row">
                  <button
                    onClick={() => {
                      if (onNavigateToDashboard) {
                        onNavigateToDashboard(acceptResult.patient_id);
                      } else if (typeof window !== "undefined") {
                        window.location.href = `/caregiver/dashboard/${acceptResult.patient_id}`;
                      }
                    }}
                    className="btn-primary"
                  >
                    Open Patient Dashboard →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

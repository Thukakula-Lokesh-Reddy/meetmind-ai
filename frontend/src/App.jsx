import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";


const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";


function App() {

  // ============================================================
  // DASHBOARD STATE
  // ============================================================

  const [meetings, setMeetings] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");


  // ============================================================
  // ACTION ITEMS STATE
  // ============================================================

  const [showActionItems, setShowActionItems] = useState(false);
  const [showMeetings, setShowMeetings] = useState(false);
  const [actionItems, setActionItems] = useState([]);

  const [actionItemsLoading, setActionItemsLoading] = useState(false);

  const [actionItemsError, setActionItemsError] = useState("");
const [updatingActionItem, setUpdatingActionItem] = useState(null);
const [sendingReminderId, setSendingReminderId] = useState(null);
const [reminderFeedback, setReminderFeedback] = useState({});

const [deletingMeetingId, setDeletingMeetingId] = useState(null);
const [retryingMeetingId, setRetryingMeetingId] = useState(null);
// ============================================================
// AI ASSISTANT STATE
// ============================================================

const [showAIAssistant, setShowAIAssistant] = useState(false);

const [aiQuestion, setAiQuestion] = useState("");

const [aiAnswer, setAiAnswer] = useState("");

const [aiSources, setAiSources] = useState([]);

const [aiLoading, setAiLoading] = useState(false);

const [aiError, setAiError] = useState("");

const [aiMeetingId, setAiMeetingId] = useState("");
  // ============================================================
  // UPLOAD STATE
  // ============================================================

  const [showUpload, setShowUpload] = useState(false);

  const [selectedFile, setSelectedFile] = useState(null);

  const [uploading, setUploading] = useState(false);

  const [uploadStatus, setUploadStatus] = useState("");


  // ============================================================
  // MEETING DETAILS STATE
  // ============================================================

  const [selectedMeetingId, setSelectedMeetingId] = useState(null);

  const [meetingDetails, setMeetingDetails] = useState(null);

  const [detailsLoading, setDetailsLoading] = useState(false);

  const [detailsError, setDetailsError] = useState("");


  // ============================================================
  // LOAD MEETINGS
  // ============================================================

  useEffect(() => {

    fetchMeetings();

  }, []);


  const fetchMeetings = async () => {

    try {

      setError("");

      const response = await axios.get(
        `${API_URL}/meetings`
      );

      setMeetings(response.data);

      setLoading(false);

    } catch (error) {

      console.error(error);

      setError(
        "Unable to connect to the backend."
      );

      setLoading(false);
    }
  };


  // ============================================================
  // WAIT FOR BACKGROUND PROCESSING
  // ============================================================

  const waitForMeetingProcessing = async (meetingId) => {

    const maxAttempts = 120;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {

      const response = await axios.get(
        `${API_URL}/meetings/${meetingId}`
      );

      const meeting = response.data;

      if (meeting.processing_status === "Analyzed") {
        return meeting;
      }

      if (meeting.processing_status === "Failed") {
        throw new Error(
          "Meeting processing failed. You can retry it from the Meetings page."
        );
      }

      await new Promise((resolve) =>
        setTimeout(resolve, 3000)
      );
    }

    throw new Error(
      "Meeting processing is taking longer than expected."
    );
  };


  // ============================================================
  // RETRY FAILED MEETING
  // ============================================================

  const retryMeeting = async (meetingId) => {

    try {

      setRetryingMeetingId(meetingId);
      setError("");

      await axios.post(
        `${API_URL}/meetings/${meetingId}/retry`
      );

      await fetchMeetings();

      await waitForMeetingProcessing(
        meetingId
      );

      await fetchMeetings();

    } catch (error) {

      console.error(
        "Meeting retry failed:",
        error
      );

      await fetchMeetings();

      alert(
        error.response?.data?.detail ||
        error.message ||
        "Meeting retry failed."
      );

    } finally {

      setRetryingMeetingId(null);

    }
  };


  // ============================================================
  // REFRESH PROCESSING MEETINGS
  // ============================================================

  useEffect(() => {

    const hasProcessingMeetings = meetings.some(
      (meeting) =>
        meeting.processing_status === "Processing"
    );

    if (!hasProcessingMeetings) {
      return;
    }

    const interval = setInterval(() => {
      fetchMeetings();
    }, 5000);

    return () => {
      clearInterval(interval);
    };

  }, [meetings]);


  // ============================================================
  // REFRESH OPEN MEETING DETAILS WHILE PROCESSING
  // ============================================================

  useEffect(() => {

    if (
      selectedMeetingId === null ||
      meetingDetails?.processing_status !== "Processing"
    ) {
      return;
    }

    const interval = setInterval(async () => {

      try {

        const response = await axios.get(
          `${API_URL}/meetings/${selectedMeetingId}`
        );

        setMeetingDetails(
          response.data
        );

        if (
          response.data.processing_status !== "Processing"
        ) {
          await fetchMeetings();
        }

      } catch (error) {

        console.error(
          "Failed to refresh meeting details:",
          error
        );

      }

    }, 5000);

    return () => {
      clearInterval(interval);
    };

  }, [
    selectedMeetingId,
    meetingDetails?.processing_status
  ]);


  // ============================================================
  // ACTION ITEM COUNT
  // ============================================================

  const getActionCount = (meeting) => {

    if (!meeting.action_items) {
      return 0;
    }

    try {

      return JSON.parse(
        meeting.action_items
      ).length;

    } catch {

      return 0;
    }
  };


  // ============================================================
  // DECISION COUNT
  // ============================================================

  const getDecisionCount = (meeting) => {

    if (!meeting.decisions) {
      return 0;
    }

    try {

      return JSON.parse(
        meeting.decisions
      ).length;

    } catch {

      return 0;
    }
  };


  // ============================================================
  // DASHBOARD STATISTICS
  // ============================================================

  const totalActions = meetings.reduce(
    (total, meeting) =>
      total + getActionCount(meeting),
    0
  );


  const totalDecisions = meetings.reduce(
    (total, meeting) =>
      total + getDecisionCount(meeting),
    0
  );


  // ============================================================
  // OPEN MEETING DETAILS
  // ============================================================

  const openMeeting = async (meetingId) => {

    try {
      setShowMeetings(false);
      setShowActionItems(false);
      setShowAIAssistant(false);
      setSelectedMeetingId(meetingId);

      setMeetingDetails(null);

      setDetailsLoading(true);

      setDetailsError("");

      const response = await axios.get(
        `${API_URL}/meetings/${meetingId}`
      );

      setMeetingDetails(
        response.data
      );

      setDetailsLoading(false);

    } catch (error) {

      console.error(error);

      setDetailsError(
        "Unable to load meeting details."
      );

      setDetailsLoading(false);
    }
  };

  // ============================================================
  // OPEN MEETINGS PAGE
  // ============================================================

  const openMeetings = () => {

    setShowMeetings(true);

    setShowActionItems(false);

    setShowAIAssistant(false);

    setSelectedMeetingId(null);

    setMeetingDetails(null);

    setDetailsError("");

  };
  // ============================================================
  // CLOSE MEETING DETAILS
  // ============================================================

  const closeMeetingDetails = () => {

    setSelectedMeetingId(null);

    setMeetingDetails(null);

    setDetailsError("");
  };


  // ============================================================
  // LOAD ACTION ITEMS
  // ============================================================

  const fetchActionItems = async () => {

    try {

      setActionItemsLoading(true);

      setActionItemsError("");

      const response = await axios.get(
        `${API_URL}/action-items`
      );

      setActionItems(response.data);

    } catch (error) {

      console.error(error);

      setActionItemsError(
        "Unable to load action items."
      );

    } finally {

      setActionItemsLoading(false);

    }
  };


  // ============================================================
  // UPDATE ACTION ITEM STATUS
  // ============================================================

  const updateActionItemStatus = async (
    actionItemId,
    newStatus
  ) => {

    try {

      setUpdatingActionItem(actionItemId);

      await axios.put(
        `${API_URL}/action-items/${actionItemId}/status`,
        {
          status: newStatus
        }
      );

      setActionItems((previousItems) =>
        previousItems.map((item) =>
          item.id === actionItemId
            ? {
                ...item,
                status: newStatus
              }
            : item
        )
      );

    } catch (error) {

      console.error(
        "Failed to update action item status:",
        error
      );

      alert(
        "Failed to update action item status. Please check the backend."
      );

    } finally {

      setUpdatingActionItem(null);

    }
  };

  // ============================================================
// SEND ACTION ITEM REMINDER
// ============================================================

const sendActionItemReminder = async (actionItemId) => {
  try {
    setSendingReminderId(actionItemId);

    setReminderFeedback((previous) => ({
      ...previous,
      [actionItemId]: {
        type: "info",
        message: "Sending reminder..."
      }
    }));

    const response = await axios.post(
      `${API_URL}/action-items/${actionItemId}/send-reminder`
    );

    setReminderFeedback((previous) => ({
      ...previous,
      [actionItemId]: {
        type: "success",
        message:
          response.data.message ||
          "Reminder sent successfully."
      }
    }));

  } catch (error) {
    console.error("Failed to send reminder:", error);

    setReminderFeedback((previous) => ({
      ...previous,
      [actionItemId]: {
        type: "error",
        message:
          error.response?.data?.detail ||
          "Unable to send reminder. Please try again."
      }
    }));

  } finally {
    setSendingReminderId(null);
  }
};


  // ============================================================
  // CLOSE ACTION ITEMS
  // ============================================================

  const closeActionItems = () => {

    setShowActionItems(false);

  };


  // ============================================================
  // AI ASSISTANT
  // ============================================================

  const askAIAssistant = async () => {

    const question = aiQuestion.trim();

    if (!question) {
      return;
    }

    try {

      setAiLoading(true);
      setAiError("");
      setAiAnswer("");
      setAiSources([]);

      const response = await axios.post(
        `${API_URL}/chat`,
        {
          question: question,
          meeting_id: aiMeetingId
            ? Number(aiMeetingId)
            : null
        }
      );

      setAiAnswer(
        response.data.answer || "No answer returned."
      );

      const sources = response.data.sources || [];

      const uniqueSources = Array.from(
        new Map(
          sources.map((source) => [
            source.meeting_id,
            source
          ])
        ).values()
      );

      setAiSources(uniqueSources);

    } catch (error) {

      console.error(
        "AI Assistant error:",
        error
      );

      setAiError(
        "Unable to get an answer. Please try again."
      );

    } finally {

      setAiLoading(false);

    }

  };


  const closeAIAssistant = () => {

    setShowAIAssistant(false);
    setAiQuestion("");
    setAiAnswer("");
    setAiSources([]);
    setAiError("");
    setAiMeetingId("");

  };


  // ============================================================
  // DELETE MEETING
  // ============================================================

  const deleteMeeting = async (meetingId, meetingTitle) => {

    const confirmed = window.confirm(
      `Are you sure you want to delete "${meetingTitle}"?\n\n` +
      "This will permanently delete the meeting, transcript, " +
      "participants, action items, and uploaded recording."
    );

    if (!confirmed) {
      return;
    }

    try {

      setDeletingMeetingId(meetingId);
      setError("");

      await axios.delete(
        `${API_URL}/meetings/${meetingId}`
      );

      setMeetings((previousMeetings) =>
        previousMeetings.filter(
          (meeting) => meeting.id !== meetingId
        )
      );

      if (selectedMeetingId === meetingId) {
        setSelectedMeetingId(null);
        setMeetingDetails(null);
      }

    } catch (error) {

      console.error(
        "Failed to delete meeting:",
        error
      );

      alert(
        "Failed to delete the meeting. Please try again."
      );

    } finally {

      setDeletingMeetingId(null);

    }
  };


  // ============================================================
  // FILE SELECTION
  // ============================================================

  const handleFileChange = (event) => {

    const file = event.target.files[0];

    if (file) {

      setSelectedFile(file);

      setUploadStatus("");
    }
  };


  // ============================================================
  // UPLOAD MEETING
  // ============================================================

  const handleUpload = async () => {

    if (!selectedFile) {

      setUploadStatus(
        "Please select a meeting file."
      );

      return;
    }


    try {

      setUploading(true);

      setUploadStatus(
        "Uploading meeting..."
      );


      // --------------------------------------------------------
      // Upload file
      // --------------------------------------------------------

      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );


      const uploadResponse = await axios.post(
        `${API_URL}/meetings/upload`,
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );


      // --------------------------------------------------------
      // Background processing has started
      // --------------------------------------------------------

      const meetingId =
        uploadResponse.data.meeting_id;

      console.log(
        `Meeting ${meetingId} uploaded successfully. ` +
        "Background processing started."
      );


      setUploadStatus(
        "Meeting uploaded. AI processing has started..."
      );


      // Show the new meeting immediately with
      // Processing status.

      await fetchMeetings();


      // Wait until the backend finishes WhisperX + Gemini.

      await waitForMeetingProcessing(
        meetingId
      );


      setUploadStatus(
        "Analysis complete!"
      );


      await fetchMeetings();


      setTimeout(() => {

        setShowUpload(false);

        setSelectedFile(null);

        setUploadStatus("");

      }, 1000);


    } catch (error) {

      console.error(
        "Meeting upload failed:",
        error
      );

      setUploadStatus(
        error.response?.data?.detail ||
        error.message ||
        "Something went wrong while processing the meeting."
      );

      await fetchMeetings();

    } finally {

      setUploading(false);

    }
  };


  // ============================================================
  // CLOSE UPLOAD MODAL
  // ============================================================

  const closeUploadModal = () => {

    if (uploading) {
      return;
    }

    setShowUpload(false);

    setSelectedFile(null);

    setUploadStatus("");
  };

  // ============================================================
// MEETINGS PAGE
// ============================================================

if (showMeetings) {

  return (

    <div className="app">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">

            <img
              src="/meetmind-logo.png"
              alt="MeetMind AI logo"
            />

          </div>

          <div>

            <h2>MeetMind AI</h2>

            <p>Meeting Intelligence</p>

          </div>

        </div>


        <div className="nav-section">

          <p className="nav-label">
            WORKSPACE
          </p>

          <nav>

            <button
              className="nav-link"
              onClick={() => {
                setShowMeetings(false);
              }}
            >

              <span className="nav-icon">
                ⌂
              </span>

              <span>
                Overview
              </span>

            </button>



            <button
              className="nav-link active"
              onClick={openMeetings}
            >

              <span className="nav-icon">
                ◫
              </span>

              <span>
                Meetings
              </span>

              <span className="nav-count">
                {meetings.length}
              </span>

            </button>


            <button
              className="nav-link"
              onClick={() => {

                setShowMeetings(false);

                setShowActionItems(true);

                fetchActionItems();

              }}
            >

              <span className="nav-icon">
                ✓
              </span>

              <span>
                Action Items
              </span>

            </button>


            <button
              className="nav-link"
              onClick={() => {

                setShowMeetings(false);

                setShowAIAssistant(true);

              }}
            >

              <span className="nav-icon">
                ✦
              </span>

              <span>
                AI Assistant
              </span>

              <span className="ai-badge">
                AI
              </span>

            </button>

          </nav>

        </div>


        <div className="nav-section secondary">

          <p className="nav-label">
            SYSTEM
          </p>

          <nav>

            <button className="nav-link">

              <span className="nav-icon">
                ⌕
              </span>

              <span>
                Search
              </span>

            </button>


            <button className="nav-link">

              <span className="nav-icon">
                ⚙
              </span>

              <span>
                Settings
              </span>

            </button>

          </nav>

        </div>


        <div className="sidebar-bottom">

          <div className="ai-status">

            <div className="status-dot"></div>

            <div>

              <strong>
                AI Engine Online
              </strong>

              <span>
                Ready to analyze meetings
              </span>

            </div>

          </div>


          <div className="user-card">

            <div className="user-avatar">
              L
            </div>

            <div className="user-info">

              <strong>
                Lokesh
              </strong>

              <span>
                Personal workspace
              </span>

            </div>

            <span className="user-menu">
              •••
            </span>

          </div>

        </div>

      </aside>


      <main className="main-content">

        <header className="topbar">

          <div className="breadcrumb">

            Workspace

            <span>
              /
            </span>

            <strong>
              Meetings
            </strong>

          </div>


          <div className="topbar-actions">

            <button className="icon-button">
              ⌕
            </button>

            <button className="icon-button notification">
              ♢
              <span></span>
            </button>

            <div className="top-avatar">
              L
            </div>

          </div>

        </header>


        <section style={{ padding: "32px" }}>

          <div
            style={{
              marginBottom: "28px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              gap: "20px"
            }}
          >

            <div>

              <div className="eyebrow">

                <span className="live-dot"></span>

                MEETING INTELLIGENCE

              </div>

              <h1 style={{ marginBottom: "10px" }}>
                Meetings
              </h1>

              <p
                style={{
                  maxWidth: "700px",
                  opacity: 0.7
                }}
              >
                Browse your meeting history and open
                any meeting to view its AI-generated
                intelligence.
              </p>

            </div>


            <button
              className="primary-button"
              onClick={() => setShowUpload(true)}
            >

              <span>
                ＋
              </span>

              Upload Meeting

            </button>

          </div>


          {loading && (

            <div className="loading-state">

              <div className="spinner"></div>

              Loading meetings...

            </div>

          )}


          {error && (

            <div className="error-state">
              {error}
            </div>

          )}


          {!loading &&
            !error &&
            meetings.length === 0 && (

              <div className="empty-state">

                <div className="empty-icon">
                  ◫
                </div>

                <h3>
                  No meetings yet
                </h3>

                <p>
                  Upload your first meeting
                  to get started.
                </p>

              </div>

          )}


          {!loading &&
            !error &&
            meetings.length > 0 && (

              <div className="meetings-panel">

                <div className="panel-header">

                  <div>

                    <div className="panel-title">
                      All Meetings
                    </div>

                    <div className="panel-subtitle">
                      {meetings.length} meeting
                      {meetings.length === 1 ? "" : "s"}
                      in your workspace
                    </div>

                  </div>

                </div>


                <div className="meetings-list">

                  {meetings.map((meeting) => (

                    <div
                      className="meeting-item"
                      key={meeting.id}
                    >

                      <div className="meeting-main">

                        <div className="meeting-avatar">
                          🎙
                        </div>


                        <div className="meeting-details">

                          <h3>
                            {meeting.title}
                          </h3>

                          <span>
                            Meeting #{meeting.id}
                          </span>

                        </div>

                      </div>


                      <div className="meeting-stats">

                        <div>

                          <strong>
                            {getActionCount(meeting)}
                          </strong>

                          <span>
                            Actions
                          </span>

                        </div>


                        <div>

                          <strong>
                            {getDecisionCount(meeting)}
                          </strong>

                          <span>
                            Decisions
                          </span>

                        </div>

                      </div>


                      <div
                        className={`meeting-status ${
                          meeting.processing_status === "Processing"
                            ? "meeting-status-processing"
                            : meeting.processing_status === "Failed"
                              ? "meeting-status-failed"
                              : ""
                        }`}
                      >

                        <span className="status-dot-small"></span>

                        {meeting.processing_status === "Processing"
                          ? "Processing"
                          : meeting.processing_status === "Failed"
                            ? "Failed"
                            : "Analyzed"}

                      </div>


                      <div className="meeting-actions">

                        {meeting.processing_status === "Failed" && (

                          <button
                            className="retry-meeting-button"
                            onClick={(event) => {
                              event.stopPropagation();

                              retryMeeting(
                                meeting.id
                              );
                            }}
                            disabled={
                              retryingMeetingId === meeting.id
                            }
                            title="Retry meeting analysis"
                          >
                            {retryingMeetingId === meeting.id
                              ? "..."
                              : "Retry"}
                          </button>

                        )}

                        <button
                          className="delete-meeting-button"
                          onClick={(event) => {
                            event.stopPropagation();
                            deleteMeeting(
                              meeting.id,
                              meeting.title
                            );
                          }}
                          disabled={
                            deletingMeetingId === meeting.id
                          }
                          title="Delete meeting"
                          aria-label={`Delete ${meeting.title}`}
                        >
                          {deletingMeetingId === meeting.id
                            ? "..."
                            : "🗑️"}
                        </button>

                        <button
                          className="arrow-button"
                          onClick={() =>
                            openMeeting(meeting.id)
                          }
                          disabled={
                            deletingMeetingId === meeting.id
                          }
                          title="Open meeting"
                          aria-label={`Open ${meeting.title}`}
                        >
                          →
                        </button>

                      </div>

                    </div>

                  ))}

                </div>

              </div>

          )}

        </section>



      {showUpload && (

        <div
          className="modal-overlay"
          onClick={closeUploadModal}
        >

          <div
            className="upload-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <button
              className="modal-close"
              onClick={closeUploadModal}
              disabled={uploading}
            >
              ×
            </button>


            <div className="modal-icon">
              🎙
            </div>


            <h2>
              Analyze a meeting
            </h2>


            <p className="modal-description">

              Upload your meeting recording and
              MeetMind AI will process the transcript,
              summary, decisions and action items in
              the background.

            </p>


            <label className="drop-zone">

              <input
                type="file"
                accept=".wav,.mp3,.m4a,.mp4,.webm,.ogg"
                onChange={handleFileChange}
                disabled={uploading}
              />


              <div className="upload-cloud">
                ↑
              </div>


              <strong>

                {selectedFile
                  ? selectedFile.name
                  : "Choose a meeting recording"}

              </strong>


              <span>
                WAV, MP3, M4A, MP4, WEBM
              </span>

            </label>


            {uploadStatus && (

              <div className="upload-status">

                {uploading && (
                  <div className="mini-spinner"></div>
                )}

                {uploadStatus}

              </div>

            )}


            <button
              className="modal-upload-button"
              onClick={handleUpload}
              disabled={
                uploading ||
                !selectedFile
              }
            >

              {uploading
                ? "Uploading meeting..."
                : "Upload Meeting"}

            </button>


            <p className="secure-note">

              ✦ Your meeting is processed by
              MeetMind AI.

            </p>

          </div>

        </div>

      )}
      </main>

    </div>

  );
}
  // ============================================================
  // ACTION ITEMS PAGE
  // ============================================================

  if (showActionItems) {

    return (

      <div className="app">

        <aside className="sidebar">

          <div className="brand">

            <div className="brand-mark">

              <img
                src="/meetmind-logo.png"
                alt="MeetMind AI logo"
              />

            </div>

            <div>

              <h2>MeetMind AI</h2>

              <p>Meeting Intelligence</p>

            </div>

          </div>


          <div className="nav-section">

            <p className="nav-label">WORKSPACE</p>

            <nav>

              <button
                className="nav-link"
                onClick={closeActionItems}
              >
                <span className="nav-icon">⌂</span>
                <span>Overview</span>
              </button>

              <button
                className="nav-link"
                onClick={closeActionItems}
              >
                <span className="nav-icon">◫</span>
                <span>Meetings</span>
                <span className="nav-count">
                  {meetings.length}
                </span>
              </button>

              <button className="nav-link active">
                <span className="nav-icon">✓</span>
                <span>Action Items</span>
              </button>

              <button className="nav-link">
                <span className="nav-icon">✦</span>
                <span>AI Assistant</span>
                <span className="ai-badge">AI</span>
              </button>

            </nav>

          </div>


          <div className="nav-section secondary">

            <p className="nav-label">SYSTEM</p>

            <nav>

              <button className="nav-link">
                <span className="nav-icon">⌕</span>
                <span>Search</span>
              </button>

              <button className="nav-link">
                <span className="nav-icon">⚙</span>
                <span>Settings</span>
              </button>

            </nav>

          </div>


          <div className="sidebar-bottom">

            <div className="ai-status">
              <div className="status-dot"></div>
              <div>
                <strong>AI Engine Online</strong>
                <span>Ready to analyze meetings</span>
              </div>
            </div>

            <div className="user-card">
              <div className="user-avatar">L</div>
              <div className="user-info">
                <strong>Lokesh</strong>
                <span>Personal workspace</span>
              </div>
              <span className="user-menu">•••</span>
            </div>

          </div>

        </aside>


        <main className="main-content">

          <header className="topbar">

            <div className="breadcrumb">
              Workspace
              <span>/</span>
              <strong>Action Items</strong>
            </div>

            <div className="topbar-actions">
              <button className="icon-button">⌕</button>
              <button className="icon-button notification">
                ♢
                <span></span>
              </button>
              <div className="top-avatar">L</div>
            </div>

          </header>


          <section style={{ padding: "32px" }}>

            <div style={{ marginBottom: "28px" }}>
              <div className="eyebrow">
                <span className="live-dot"></span>
                MEETING ACTION TRACKER
              </div>

              <h1 style={{ marginBottom: "10px" }}>
                Action Items
              </h1>

              <p style={{ maxWidth: "700px", opacity: 0.7 }}>
                Track tasks extracted from your meetings, including owners, deadlines, and current status.
              </p>
            </div>


            {actionItemsLoading && (
              <div style={{ padding: "40px 0" }}>
                Loading action items...
              </div>
            )}


            {actionItemsError && (
              <div style={{ padding: "20px 0" }}>
                {actionItemsError}
              </div>
            )}


            {!actionItemsLoading && !actionItemsError && (

              <div style={{
                background: "rgba(20, 21, 31, 0.92)",
                borderRadius: "18px",
                overflow: "hidden",
                border: "1px solid rgba(255,255,255,0.08)",
                boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
                color: "#f5f5f7"
              }}>

                <div style={{
                  padding: "24px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  borderBottom: "1px solid rgba(255,255,255,0.08)"
                }}>
                  <div>
                    <strong style={{
                      fontSize: "18px",
                      color: "#f5f5f7"
                    }}>
                      All Action Items
                    </strong>

                    <div style={{
                      color: "rgba(245,245,247,0.58)",
                      marginTop: "6px"
                    }}>
                      {actionItems.length} task{actionItems.length === 1 ? "" : "s"} extracted from meetings
                    </div>
                  </div>
                </div>

                {actionItems.length === 0 ? (
                  <div style={{
                    padding: "40px 24px",
                    color: "rgba(245,245,247,0.65)"
                  }}>
                    No action items found. Analyze a meeting to create tasks.
                  </div>
                ) : (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      color: "#f5f5f7"
                    }}>
                      <thead>
                        <tr style={{
                          textAlign: "left",
                          borderBottom: "1px solid rgba(255,255,255,0.08)",
                          color: "rgba(245,245,247,0.58)"
                        }}>
                          <th style={{ padding: "16px 24px", fontWeight: 600 }}>Task</th>
                          <th style={{ padding: "16px 24px", fontWeight: 600 }}>Owner</th>
                          <th style={{ padding: "16px 24px", fontWeight: 600 }}>Deadline</th>
                          <th style={{ padding: "16px 24px", fontWeight: 600 }}>Status</th>
                          <th style={{ padding: "16px 24px", fontWeight: 600 }}>
                            Reminder
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        {actionItems.map((item) => (
                          <tr
                            key={item.id}
                            style={{
                              borderBottom: "1px solid rgba(255,255,255,0.06)"
                            }}
                          >
                            <td style={{
                              padding: "18px 24px",
                              minWidth: "320px",
                              color: "#f5f5f7"
                            }}>
                              {item.task}
                            </td>

                            <td style={{
                              padding: "18px 24px",
                              color: "rgba(245,245,247,0.78)"
                            }}>
                              {item.owner || "Unassigned"}
                            </td>

                            <td style={{
                              padding: "18px 24px",
                              color: "rgba(245,245,247,0.78)"
                            }}>
                              {item.deadline || "No deadline"}
                            </td>

                            <td style={{ padding: "18px 24px" }}>
                              <select
                                value={item.status || "Pending"}
                                disabled={
                                  updatingActionItem === item.id
                                }
                                onChange={(event) =>
                                  updateActionItemStatus(
                                    item.id,
                                    event.target.value
                                  )
                                }
                                className="action-status-select"
                                style={{
                                  color:
                                    item.status === "Completed"
                                      ? "#4ade80"
                                      : item.status === "In Progress"
                                        ? "#60a5fa"
                                        : "#facc15",
                                  background:
                                    item.status === "Completed"
                                      ? "rgba(74, 222, 128, 0.10)"
                                      : item.status === "In Progress"
                                        ? "rgba(96, 165, 250, 0.10)"
                                        : "rgba(250, 204, 21, 0.10)",
                                  borderColor:
                                    item.status === "Completed"
                                      ? "rgba(74, 222, 128, 0.35)"
                                      : item.status === "In Progress"
                                        ? "rgba(96, 165, 250, 0.35)"
                                        : "rgba(250, 204, 21, 0.35)",
                                  boxShadow:
                                    item.status === "Completed"
                                      ? "0 0 18px rgba(74, 222, 128, 0.08)"
                                      : item.status === "In Progress"
                                        ? "0 0 18px rgba(96, 165, 250, 0.08)"
                                        : "0 0 18px rgba(250, 204, 21, 0.08)",
                                  padding: "7px 12px",
                                  paddingRight: "12px",
                                  borderRadius: "999px",
                                  fontSize: "12px",
                                  fontWeight: 600,
                                  cursor:
                                    updatingActionItem === item.id
                                      ? "wait"
                                      : "pointer",
                                  outline: "none",
                                  appearance: "none",
                                  WebkitAppearance: "none",
                                  MozAppearance: "none"
                                }}
                              >
                                <option
                                  value="Pending"
                                  style={{
                                    color: "#facc15",
                                    background: "#242531"
                                  }}
                                >
                                  Pending
                                </option>

                                <option
                                  value="In Progress"
                                  style={{
                                    color: "#60a5fa",
                                    background: "#242531"
                                  }}
                                >
                                  In Progress
                                </option>

                                <option
                                  value="Completed"
                                  style={{
                                    color: "#4ade80",
                                    background: "#242531"
                                  }}
                                >
                                  Completed
                                </option>
                              </select>
                            </td>

                            <td style={{ padding: "18px 24px", minWidth: "190px" }}>
                              <button
                                type="button"
                                onClick={() => sendActionItemReminder(item.id)}
                                disabled={
                                  item.status === "Completed" ||
                                  sendingReminderId !== null
                                }
                                title={
                                  item.status === "Completed"
                                    ? "Completed tasks cannot receive reminders"
                                    : "Send an email reminder to the task owner"
                                }
                                style={{
                                  padding: "9px 12px",
                                  borderRadius: "8px",
                                  border: "1px solid rgba(126, 92, 245, 0.45)",
                                  background: "rgba(126, 92, 245, 0.14)",
                                  color: "#c1b5ff",
                                  fontSize: "12px",
                                  fontWeight: 600,
                                  cursor:
                                    item.status === "Completed" ||
                                    sendingReminderId !== null
                                      ? "not-allowed"
                                      : "pointer",
                                  opacity:
                                    item.status === "Completed" ||
                                    sendingReminderId !== null
                                      ? 0.55
                                      : 1
                                }}
                              >
                                {sendingReminderId === item.id
                                  ? "Sending..."
                                  : "✉ Send Reminder"}
                              </button>

                              {reminderFeedback[item.id] && (
                                <div
                                  role="status"
                                  style={{
                                    marginTop: "8px",
                                    maxWidth: "220px",
                                    fontSize: "11px",
                                    lineHeight: 1.5,
                                    overflowWrap: "anywhere",
                                    color:
                                      reminderFeedback[item.id].type === "success"
                                        ? "#4ade80"
                                        : reminderFeedback[item.id].type === "error"
                                          ? "#fca5a5"
                                          : "#c1b5ff"
                                  }}
                                >
                                  {reminderFeedback[item.id].message}
                                </div>
                              )}
                            </td>

                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

              </div>

            )}

          </section>

        </main>

      </div>

    );
  }


  // ============================================================
  // MEETING DETAILS PAGE
  // ============================================================

  if (selectedMeetingId !== null) {

    return (

      <div className="app">

        <aside className="sidebar">

          <div className="brand">

            <div className="brand-mark">

              <img
                src="/meetmind-logo.png"
                alt="MeetMind AI logo"
              />

            </div>

            <div>

              <h2>MeetMind AI</h2>

              <p>
                Meeting Intelligence
              </p>

            </div>

          </div>


          <div className="nav-section">

            <p className="nav-label">
              WORKSPACE
            </p>

            <nav>

              <button
                className="nav-link active"
                onClick={closeMeetingDetails}
              >
                <span className="nav-icon">
                  ⌂
                </span>

                <span>
                  Overview
                </span>

              </button>


              <button
                className="nav-link"
                onClick={closeMeetingDetails}
              >

                <span className="nav-icon">
                  ◫
                </span>

                <span>
                  Meetings
                </span>

                <span className="nav-count">
                  {meetings.length}
                </span>

              </button>


              <button
                className="nav-link"
                onClick={() => {
                  setSelectedMeetingId(null);
                  setShowActionItems(true);
                  fetchActionItems();
                }}
              >

                <span className="nav-icon">
                  ✓
                </span>

                <span>
                  Action Items
                </span>

              </button>


              <button className="nav-link">

                <span className="nav-icon">
                  ✦
                </span>

                <span>
                  AI Assistant
                </span>

                <span className="ai-badge">
                  AI
                </span>

              </button>

            </nav>

          </div>


          <div className="sidebar-bottom">

            <div className="ai-status">

              <div className="status-dot"></div>

              <div>

                <strong>
                  AI Engine Online
                </strong>

                <span>
                  Ready to analyze meetings
                </span>

              </div>

            </div>


            <div className="user-card">

              <div className="user-avatar">
                L
              </div>

              <div className="user-info">

                <strong>
                  Lokesh
                </strong>

                <span>
                  Personal workspace
                </span>

              </div>

              <span className="user-menu">
                •••
              </span>

            </div>

          </div>

        </aside>


        <main className="main-content">

          <header className="topbar">

            <div className="breadcrumb">

              Workspace

              <span>/</span>

              <button
                className="breadcrumb-button"
                onClick={closeMeetingDetails}
              >
                Meetings
              </button>

              <span>/</span>

              <strong>
                Details
              </strong>

            </div>


            <div className="topbar-actions">

              <button className="icon-button">
                ⌕
              </button>

              <button className="icon-button notification">
                ♢
                <span></span>
              </button>

              <div className="top-avatar">
                L
              </div>

            </div>

          </header>


          <section className="details-page">

            {detailsLoading && (

              <div className="details-loading">

                <div className="spinner"></div>

                Loading meeting...

              </div>

            )}


            {detailsError && (

              <div className="error-state">

                {detailsError}

              </div>

            )}


            {meetingDetails && (

              <>

                {/* ==================================================
                    DETAILS HEADER
                ================================================== */}

                <div className="details-header">

                  <button
                    className="back-button"
                    onClick={closeMeetingDetails}
                  >
                    ← Back to meetings
                  </button>


                  <div className="details-title-row">

                    <div>

                      <div className="details-eyebrow">

                        MEETING #{meetingDetails.id}

                        <span>
                          •
                        </span>

                        {meetingDetails.processing_status === "Processing"
                          ? "PROCESSING"
                          : meetingDetails.processing_status === "Failed"
                            ? "PROCESSING FAILED"
                            : "AI ANALYZED"}

                      </div>


                      <h1>
                        {meetingDetails.title}
                      </h1>


                      <p>
                        Meeting intelligence generated
                        by MeetMind AI
                      </p>

                    </div>


                    <div
                      className={`analyzed-badge ${
                        meetingDetails.processing_status === "Processing"
                          ? "meeting-status-processing"
                          : meetingDetails.processing_status === "Failed"
                            ? "meeting-status-failed"
                            : ""
                      }`}
                    >

                      <span className="status-dot-small"></span>

                      {meetingDetails.processing_status === "Processing"
                        ? "Processing"
                        : meetingDetails.processing_status === "Failed"
                          ? "Failed"
                          : "Analyzed"}

                    </div>

                  </div>

                </div>


                {meetingDetails.processing_status === "Processing" && (

                  <div className="meeting-processing-notice">

                    <div className="mini-spinner"></div>

                    <div>

                      <strong>
                        AI processing in progress
                      </strong>

                      <span>
                        WhisperX is transcribing the meeting and
                        Gemini will generate the meeting intelligence.
                        This page will update automatically.
                      </span>

                    </div>

                  </div>

                )}

                {meetingDetails.processing_status === "Failed" && (

                  <div className="meeting-processing-notice meeting-processing-notice-error">

                    <div>

                      <strong>
                        Meeting processing failed
                      </strong>

                      <span>
                        The recording was uploaded, but AI processing
                        could not be completed.
                      </span>

                      <button
                        className="retry-meeting-button"
                        onClick={() =>
                          retryMeeting(
                            meetingDetails.id
                          )
                        }
                        disabled={
                          retryingMeetingId === meetingDetails.id
                        }
                        style={{
                          marginTop: "12px"
                        }}
                      >
                        {retryingMeetingId === meetingDetails.id
                          ? "Retrying..."
                          : "Retry Analysis"}
                      </button>

                    </div>

                  </div>

                )}

                {/* ==================================================
                    SUMMARY STAT CARDS
                ================================================== */}

                <div className="details-stats-grid">

                  <div className="details-stat-card">

                    <span className="details-stat-icon">
                      ◉
                    </span>

                    <div>

                      <strong>
                        {meetingDetails.participants.length}
                      </strong>

                      <span>
                        Participants
                      </span>

                    </div>

                  </div>


                  <div className="details-stat-card">

                    <span className="details-stat-icon">
                      ◆
                    </span>

                    <div>

                      <strong>
                        {meetingDetails.decisions.length}
                      </strong>

                      <span>
                        Decisions
                      </span>

                    </div>

                  </div>


                  <div className="details-stat-card">

                    <span className="details-stat-icon">
                      ✓
                    </span>

                    <div>

                      <strong>
                        {meetingDetails.action_items.length}
                      </strong>

                      <span>
                        Action Items
                      </span>

                    </div>

                  </div>

                </div>


                {/* ==================================================
                    AI SUMMARY
                ================================================== */}

                <section className="details-card summary-card">

                  <div className="details-card-header">

                    <div>

                      <span className="section-kicker">
                        AI INSIGHT
                      </span>

                      <h2>
                        Meeting Summary
                      </h2>

                    </div>

                    <div className="summary-ai-icon">
                      ✦
                    </div>

                  </div>


                  <p className="summary-text">

                    {meetingDetails.summary ||
                      "No summary available."}

                  </p>

                </section>


                {/* ==================================================
                    PARTICIPANTS
                ================================================== */}

                <section className="details-card">

                  <div className="details-card-header">

                    <div>

                      <span className="section-kicker">
                        PEOPLE
                      </span>

                      <h2>
                        Participants
                      </h2>

                    </div>

                  </div>


                  <div className="participants-grid">

                    {meetingDetails.participants.map(
                      (participant) => (

                        <div
                          className="participant-card"
                          key={participant.id}
                        >

                          <div className="participant-avatar">

                            {participant.name
                              .charAt(0)
                              .toUpperCase()}

                          </div>


                          <div>

                            <strong>
                              {participant.name}
                            </strong>

                            <span>
                              Meeting participant
                            </span>

                          </div>

                        </div>

                      )
                    )}

                  </div>

                </section>


                {/* ==================================================
                    DECISIONS
                ================================================== */}

                <section className="details-card">

                  <div className="details-card-header">

                    <div>

                      <span className="section-kicker">
                        OUTCOMES
                      </span>

                      <h2>
                        Decisions
                      </h2>

                    </div>

                  </div>


                  {meetingDetails.decisions.length === 0 ? (

                    <div className="details-empty">
                      No decisions were detected.
                    </div>

                  ) : (

                    <div className="decision-list">

                      {meetingDetails.decisions.map(
                        (decision, index) => (

                          <div
                            className="decision-item"
                            key={index}
                          >

                            <div className="decision-check">
                              ✓
                            </div>

                            <p>
                              {decision}
                            </p>

                          </div>

                        )
                      )}

                    </div>

                  )}

                </section>


                {/* ==================================================
                    ACTION ITEMS
                ================================================== */}

                <section className="details-card">

                  <div className="details-card-header">

                    <div>

                      <span className="section-kicker">
                        FOLLOW-UP
                      </span>

                      <h2>
                        Action Items
                      </h2>

                    </div>


                    <span className="action-count-badge">

                      {meetingDetails.action_items.length}

                    </span>

                  </div>


                  {meetingDetails.action_items.length === 0 ? (

                    <div className="details-empty">
                      No action items were detected.
                    </div>

                  ) : (

                    <div className="action-list">

                      {meetingDetails.action_items.map(
                        (item, index) => (

                          <div
                            className="action-item"
                            key={index}
                          >

                            <div className="action-number">
                              {String(index + 1).padStart(2, "0")}
                            </div>


                            <div className="action-content">

                              <h3>
                                {item.task}
                              </h3>


                              <div className="action-meta">

                                <span className="owner-pill">

                                  <span className="owner-avatar">

                                    {item.owner
                                      ? item.owner
                                          .charAt(0)
                                          .toUpperCase()
                                      : "?"}

                                  </span>

                                  {item.owner ||
                                    "Unassigned"}

                                </span>


                                <span className="deadline-pill">

                                  ◷

                                  {item.deadline ||
                                    "No deadline"}

                                </span>

                              </div>

                            </div>

                          </div>

                        )
                      )}

                    </div>

                  )}

                </section>


                {/* ==================================================
                    TRANSCRIPT
                ================================================== */}

                <section className="details-card">

                  <div className="details-card-header">

                    <div>

                      <span className="section-kicker">
                        SOURCE
                      </span>

                      <h2>
                        Transcript
                      </h2>

                    </div>

                  </div>


                  <details className="transcript-container">

                    <summary>
                      View full meeting transcript
                    </summary>

                    <div className="transcript-text">

                      {meetingDetails.transcript ||
                        "No transcript available."}

                    </div>

                  </details>

                </section>

              </>

            )}

          </section>

        </main>

      </div>

    );

  }


  // ============================================================
  // MAIN DASHBOARD
  // ============================================================

  return (
    <>
      <style>{`
        .action-status-select {
          min-width: 112px;
          transition:
            color 0.2s ease,
            background 0.2s ease,
            border-color 0.2s ease,
            box-shadow 0.2s ease;
        }

        .action-status-select:hover {
          filter: brightness(1.08);
        }

        .action-status-select:focus {
          outline: none;
        }

        .action-status-select option {
          color: #f5f5f7;
          background: #242531;
          font-weight: 600;
        }

        .action-status-select option[value="Pending"] {
          color: #facc15;
        }

        .action-status-select option[value="In Progress"] {
          color: #60a5fa;
        }

        .action-status-select option[value="Completed"] {
          color: #4ade80;
        }


        .meeting-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-shrink: 0;
        }

        .delete-meeting-button {
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid #2a1f29;
          border-radius: 8px;
          background: #111017;
          color: #b86a78;
          font-size: 14px;
          cursor: pointer;
          transition:
            background 0.2s ease,
            border-color 0.2s ease,
            color 0.2s ease,
            transform 0.2s ease;
        }

        .delete-meeting-button:hover {
          background: #24151b;
          border-color: #6b2b3a;
          color: #ff7185;
          transform: translateY(-1px);
        }

        .delete-meeting-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .retry-meeting-button {
          border: 1px solid rgba(126, 92, 245, 0.35);
          border-radius: 8px;
          background: rgba(126, 92, 245, 0.10);
          color: #a995ff;
          padding: 7px 10px;
          font-size: 10px;
          font-weight: 600;
          cursor: pointer;
          transition:
            background 0.2s ease,
            border-color 0.2s ease,
            color 0.2s ease,
            transform 0.2s ease;
        }

        .retry-meeting-button:hover {
          background: rgba(126, 92, 245, 0.18);
          border-color: rgba(126, 92, 245, 0.55);
          color: #c1b5ff;
          transform: translateY(-1px);
        }

        .retry-meeting-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .meeting-status-processing {
          color: #facc15;
        }

        .meeting-status-failed {
          color: #ff7b7b;
        }

        .meeting-status-processing .status-dot-small {
          animation: meeting-status-pulse 1.4s ease-in-out infinite;
        }

        @keyframes meeting-status-pulse {
          0%,
          100% {
            opacity: 1;
          }

          50% {
            opacity: 0.35;
          }
        }

        .meeting-processing-notice {
          display: flex;
          align-items: flex-start;
          gap: 14px;
          margin-bottom: 24px;
          padding: 16px 18px;
          border: 1px solid rgba(250, 204, 21, 0.22);
          border-radius: 14px;
          background: rgba(250, 204, 21, 0.07);
        }

        .meeting-processing-notice strong {
          display: block;
          margin-bottom: 5px;
          color: #facc15;
          font-size: 14px;
        }

        .meeting-processing-notice span {
          display: block;
          color: rgba(255, 255, 255, 0.62);
          font-size: 13px;
          line-height: 1.5;
        }

        .meeting-processing-notice-error {
          border-color: rgba(255, 123, 123, 0.25);
          background: rgba(255, 123, 123, 0.07);
        }

        .meeting-processing-notice-error strong {
          color: #ff7b7b;
        }

        .meeting-processing-notice .mini-spinner {
          flex-shrink: 0;
          margin-top: 2px;
        }

        .ai-chat-box {
          width: 100%;
          margin-top: 22px;
        }

        .ai-chat-box input {
          width: 100%;
          box-sizing: border-box;
          padding: 14px 16px;
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.12);
          background: rgba(255, 255, 255, 0.06);
          color: white;
          outline: none;
          font-size: 14px;
          margin-bottom: 12px;
        }

        .ai-chat-box input::placeholder {
          color: rgba(255, 255, 255, 0.45);
        }

        .ai-chat-box input:focus {
          border-color: rgba(255, 255, 255, 0.3);
        }

        .ai-chat-box input:disabled {
          opacity: 0.6;
        }

        .ai-button:disabled {
          opacity: 0.6;
          cursor: wait;
        }

        .ai-answer {
          margin-top: 18px;
          padding: 18px;
          border-radius: 14px;
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .ai-answer-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 1.2px;
          margin-bottom: 10px;
          opacity: 0.6;
        }

        .ai-answer p {
          margin: 0;
          color: rgba(255, 255, 255, 0.9);
          font-size: 14px;
          line-height: 1.6;
        }

        .ai-sources {
          margin-top: 18px;
          padding-top: 14px;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .ai-sources-title {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 1px;
          opacity: 0.55;
          margin-bottom: 10px;
        }

        .ai-source {
          display: flex;
          flex-direction: column;
          gap: 3px;
          padding: 9px 0;
          font-size: 12px;
        }

        .ai-source strong {
          color: rgba(255, 255, 255, 0.85);
        }

        .ai-source span {
          color: rgba(255, 255, 255, 0.45);
        }

        .ai-error {
          margin-top: 12px;
          color: #ff8a8a;
          font-size: 13px;
        }

        .ai-close-button {
          margin-top: 12px;
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.5);
          cursor: pointer;
          font-size: 12px;
        }

        .ai-close-button:hover {
          color: white;
        }
      `}</style>

      <div className="app">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">

            <img
              src="/meetmind-logo.png"
              alt="MeetMind AI logo"
            />

          </div>

          <div>

            <h2>
              MeetMind AI
            </h2>

            <p>
              Meeting Intelligence
            </p>

          </div>

        </div>


        <div className="nav-section">

          <p className="nav-label">
            WORKSPACE
          </p>

          <nav>

            <button className="nav-link active">

              <span className="nav-icon">
                ⌂
              </span>

              <span>
                Overview
              </span>

            </button>


            <button
              className="nav-link"
              onClick={openMeetings}
            >

              <span className="nav-icon">
                ◫
              </span>

              <span>
                Meetings
              </span>

              <span className="nav-count">
                {meetings.length}
              </span>

            </button>


            <button
              className="nav-link"
              onClick={() => {
                setShowActionItems(true);
                fetchActionItems();
              }}
            >

              <span className="nav-icon">
                ✓
              </span>

              <span>
                Action Items
              </span>

            </button>


            <button
              className="nav-link"
              onClick={() => setShowAIAssistant(true)}
            >

              <span className="nav-icon">
                ✦
              </span>

              <span>
                AI Assistant
              </span>

              <span className="ai-badge">
                AI
              </span>

            </button>

          </nav>

        </div>


        <div className="nav-section secondary">

          <p className="nav-label">
            SYSTEM
          </p>

          <nav>

            <button className="nav-link">

              <span className="nav-icon">
                ⌕
              </span>

              <span>
                Search
              </span>

            </button>


            <button className="nav-link">

              <span className="nav-icon">
                ⚙
              </span>

              <span>
                Settings
              </span>

            </button>

          </nav>

        </div>


        <div className="sidebar-bottom">

          <div className="ai-status">

            <div className="status-dot"></div>

            <div>

              <strong>
                AI Engine Online
              </strong>

              <span>
                Ready to analyze meetings
              </span>

            </div>

          </div>


          <div className="user-card">

            <div className="user-avatar">
              L
            </div>

            <div className="user-info">

              <strong>
                Lokesh
              </strong>

              <span>
                Personal workspace
              </span>

            </div>

            <span className="user-menu">
              •••
            </span>

          </div>

        </div>

      </aside>


      <main className="main-content">

        <header className="topbar">

          <div className="breadcrumb">

            Workspace

            <span>
              /
            </span>

            <strong>
              Overview
            </strong>

          </div>


          <div className="topbar-actions">

            <button className="icon-button">
              ⌕
            </button>

            <button className="icon-button notification">

              ♢

              <span></span>

            </button>

            <div className="top-avatar">
              L
            </div>

          </div>

        </header>


        <section className="hero">

          <div className="hero-glow"></div>


          <div className="hero-content">

            <div className="eyebrow">

              <span className="live-dot"></span>

              AI MEETING INTELLIGENCE

            </div>


            <h1>

              Turn every meeting
              <br />

              into <span>action.</span>

            </h1>


            <p>

              Capture conversations, decisions and
              action items automatically with AI-powered
              meeting intelligence.

            </p>

          </div>


          <button
            className="primary-button"
            onClick={() => setShowUpload(true)}
          >

            <span>
              ＋
            </span>

            Upload Meeting

          </button>

        </section>


        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-top">

              <div className="stat-symbol purple-symbol">
                ◫
              </div>

              <span className="stat-trend">
                AI
              </span>

            </div>


            <div className="stat-value">
              {meetings.length}
            </div>


            <div className="stat-name">
              Total Meetings
            </div>


            <div className="stat-description">
              Meetings analyzed by AI
            </div>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <div className="stat-symbol blue-symbol">
                ✓
              </div>

              <span className="stat-trend">
                Active
              </span>

            </div>


            <div className="stat-value">
              {totalActions}
            </div>


            <div className="stat-name">
              Action Items
            </div>


            <div className="stat-description">
              Tasks identified from meetings
            </div>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <div className="stat-symbol green-symbol">
                ◆
              </div>

              <span className="stat-trend">
                Tracked
              </span>

            </div>


            <div className="stat-value">
              {totalDecisions}
            </div>


            <div className="stat-name">
              Decisions
            </div>


            <div className="stat-description">
              Important decisions captured
            </div>

          </div>

        </section>


        <section className="content-grid">

          <div className="meetings-panel">

            <div className="panel-header">

              <div>

                <div className="panel-title">
                  Recent Meetings
                </div>

                <div className="panel-subtitle">
                  Your latest AI-analyzed conversations
                </div>

              </div>


              <button
                className="text-button"
                onClick={openMeetings}
              >
                View all →
              </button>

            </div>


            <div className="meetings-list">

              {loading && (

                <div className="loading-state">

                  <div className="spinner"></div>

                  Loading meetings...

                </div>

              )}


              {error && (

                <div className="error-state">

                  {error}

                </div>

              )}


              {!loading &&
                !error &&
                meetings.length === 0 && (

                  <div className="empty-state">

                    <div className="empty-icon">
                      ◫
                    </div>

                    <h3>
                      No meetings yet
                    </h3>

                    <p>
                      Upload your first meeting
                      to get started.
                    </p>

                  </div>

                )}


              {!loading &&
                !error &&
                meetings.map((meeting) => (

                  <div
                    className="meeting-item"
                    key={meeting.id}
                  >

                    <div className="meeting-main">

                      <div className="meeting-avatar">
                        🎙
                      </div>


                      <div className="meeting-details">

                        <h3>
                          {meeting.title}
                        </h3>

                        <span>
                          Meeting #{meeting.id}
                        </span>

                      </div>

                    </div>


                    <div className="meeting-stats">

                      <div>

                        <strong>
                          {getActionCount(meeting)}
                        </strong>

                        <span>
                          Actions
                        </span>

                      </div>


                      <div>

                        <strong>
                          {getDecisionCount(meeting)}
                        </strong>

                        <span>
                          Decisions
                        </span>

                      </div>

                    </div>


                    <div
                      className={`meeting-status ${
                        meeting.processing_status === "Processing"
                          ? "meeting-status-processing"
                          : meeting.processing_status === "Failed"
                            ? "meeting-status-failed"
                            : ""
                      }`}
                    >

                      <span className="status-dot-small"></span>

                      {meeting.processing_status === "Processing"
                        ? "Processing"
                        : meeting.processing_status === "Failed"
                          ? "Failed"
                          : "Analyzed"}

                    </div>


                    <div className="meeting-actions">

                      {meeting.processing_status === "Failed" && (

                        <button
                          className="retry-meeting-button"
                          onClick={(event) => {
                            event.stopPropagation();

                            retryMeeting(
                              meeting.id
                            );
                          }}
                          disabled={
                            retryingMeetingId === meeting.id
                          }
                          title="Retry meeting analysis"
                        >
                          {retryingMeetingId === meeting.id
                            ? "..."
                            : "Retry"}
                        </button>

                      )}

                      <button
                        className="delete-meeting-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteMeeting(
                            meeting.id,
                            meeting.title
                          );
                        }}
                        disabled={
                          deletingMeetingId === meeting.id
                        }
                        title="Delete meeting"
                        aria-label={`Delete ${meeting.title}`}
                      >
                        {deletingMeetingId === meeting.id
                          ? "..."
                          : "🗑️"}
                      </button>

                      <button
                        className="arrow-button"
                        onClick={() =>
                          openMeeting(meeting.id)
                        }
                        disabled={
                          deletingMeetingId === meeting.id
                        }
                        title="Open meeting"
                        aria-label={`Open ${meeting.title}`}
                      >
                        →
                      </button>

                    </div>

                  </div>

                ))}

            </div>

          </div>


          <div className="ai-panel">

            <div className="ai-panel-glow"></div>


            <div className="ai-icon-large">
              ✦
            </div>


            <div className="ai-panel-content">

              <span className="ai-label">
                AI ASSISTANT
              </span>


              <h2>

                Ask anything
                <br />

                about your meetings.

              </h2>


              <p>

                Search across your meeting history
                and get answers using AI.

              </p>


              {!showAIAssistant ? (

                <button
                  className="ai-button"
                  onClick={() => setShowAIAssistant(true)}
                >

                  Open AI Assistant

                  <span>
                    →
                  </span>

                </button>

              ) : (

                <div className="ai-chat-box">

                  <div
                    className="ai-scope-label"
                    style={{
                      display: "block",
                      marginBottom: "8px",
                      fontSize: "11px",
                      fontWeight: 700,
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      opacity: 0.65
                    }}
                  >
                    Ask about
                  </div>

                  <select
                    value={aiMeetingId}
                    onChange={(event) =>
                      setAiMeetingId(event.target.value)
                    }
                    disabled={aiLoading}
                    style={{
                      width: "100%",
                      marginBottom: "10px",
                      padding: "11px 12px",
                      borderRadius: "10px",
                      border: "1px solid rgba(255,255,255,0.10)",
                      background: "rgba(255,255,255,0.05)",
                      color: "#f5f5f7",
                      outline: "none",
                      fontSize: "13px",
                      cursor: aiLoading ? "not-allowed" : "pointer"
                    }}
                  >
                    <option
                      value=""
                      style={{
                        background: "#242531",
                        color: "#f5f5f7"
                      }}
                    >
                      All Meetings
                    </option>

                    {meetings.map((meeting) => (
                      <option
                        key={meeting.id}
                        value={meeting.id}
                        disabled={
                          meeting.processing_status === "Processing"
                        }
                        style={{
                          background: "#242531",
                          color: "#f5f5f7"
                        }}
                      >
                        Meeting #{meeting.id} — {meeting.title}
                        {meeting.processing_status === "Processing"
                          ? " (Processing)"
                          : meeting.processing_status === "Failed"
                            ? " (Failed)"
                            : ""}
                      </option>
                    ))}
                  </select>

                  <input
                    type="text"
                    value={aiQuestion}
                    onChange={(event) =>
                      setAiQuestion(event.target.value)
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        askAIAssistant();
                      }
                    }}
                    placeholder="Ask about your meetings..."
                    disabled={aiLoading}
                  />


                  <button
                    className="ai-button"
                    onClick={askAIAssistant}
                    disabled={
                      aiLoading ||
                      !aiQuestion.trim()
                    }
                  >

                    {aiLoading
                      ? "Thinking..."
                      : "Ask AI"
                    }

                    <span>
                      →
                    </span>

                  </button>


                  {aiError && (

                    <div className="ai-error">
                      {aiError}
                    </div>

                  )}


                  {aiAnswer && (

                    <div className="ai-answer">

                      <div className="ai-answer-label">
                        AI ANSWER
                      </div>


                      <p>
                        {aiAnswer}
                      </p>


                      {aiSources.length > 0 && (

                        <div className="ai-sources">

                          <div className="ai-sources-title">
                            SOURCES
                          </div>


                          {aiSources.map(
                            (source, index) => (

                              <div
                                className="ai-source"
                                key={`${source.meeting_id}-${source.chunk_id}-${index}`}
                              >

                                <strong>
                                  Meeting #{source.meeting_id}
                                </strong>

                                <span>
                                  {source.title}
                                </span>

                              </div>

                            )
                          )}

                        </div>

                      )}

                    </div>

                  )}


                  <button
                    className="ai-close-button"
                    onClick={closeAIAssistant}
                  >
                    Close
                  </button>

                </div>

              )}

            </div>


            <div className="ai-orb orb-one"></div>

            <div className="ai-orb orb-two"></div>

          </div>

        </section>

      </main>


      {/* ========================================================
          UPLOAD MODAL
      ======================================================== */}

      {showUpload && (

        <div
          className="modal-overlay"
          onClick={closeUploadModal}
        >

          <div
            className="upload-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <button
              className="modal-close"
              onClick={closeUploadModal}
              disabled={uploading}
            >
              ×
            </button>


            <div className="modal-icon">
              🎙
            </div>


            <h2>
              Analyze a meeting
            </h2>


            <p className="modal-description">

              Upload your meeting recording and
              MeetMind AI will extract the summary,
              decisions and action items.

            </p>


            <label className="drop-zone">

              <input
                type="file"
                accept=".wav,.mp3,.m4a,.mp4,.webm,.ogg"
                onChange={handleFileChange}
                disabled={uploading}
              />


              <div className="upload-cloud">
                ↑
              </div>


              <strong>

                {selectedFile
                  ? selectedFile.name
                  : "Choose a meeting recording"}

              </strong>


              <span>
                WAV, MP3, M4A, MP4, WEBM
              </span>

            </label>


            {uploadStatus && (

              <div className="upload-status">

                {uploading && (
                  <div className="mini-spinner"></div>
                )}

                {uploadStatus}

              </div>

            )}


            <button
              className="modal-upload-button"
              onClick={handleUpload}
              disabled={
                uploading ||
                !selectedFile
              }
            >

              {uploading
                ? "Processing meeting..."
                : "Upload & Analyze"}

            </button>


            <p className="secure-note">

              ✦ Your meeting is processed by
              MeetMind AI.

            </p>

          </div>

        </div>

      )}

      </div>
    </>
  );
}


export default App;9

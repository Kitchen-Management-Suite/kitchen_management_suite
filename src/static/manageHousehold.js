/**
 * manageHousehold.js
 * Manage Households page with modals for create, join, and request management
 */

import { h, useState, useEffect, render } from './hook.js';
import { Modal, FormInput, FormTextarea, Button, Alert, useForm } from './components.js';

// ============================================================================
// Create Household Modal
// ============================================================================

function CreateHouseholdModal({ isOpen, onClose }) {
  const [form, setField, resetForm] = useForm({
    householdName: ''
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!form.householdName.trim()) {
      setError('Household name is required');
      return;
    }

    setLoading(true);
    setError(null);

    // Use form submission to the existing route
    const formEl = document.createElement('form');
    formEl.method = 'POST';
    formEl.action = '/household/create';
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'household_name';
    input.value = form.householdName.trim();
    formEl.appendChild(input);
    
    document.body.appendChild(formEl);
    formEl.submit();
  };

  const handleClose = () => {
    resetForm();
    setError(null);
    onClose();
  };

  return h(Modal, {
    isOpen,
    onClose: handleClose,
    title: 'Create New Household',
    size: 'sm',
    footer: [
      h(Button, { text: 'Cancel', variant: 'secondary', onClick: handleClose }),
      h(Button, { text: 'Create', variant: 'primary', onClick: handleSubmit, loading })
    ]
  },
    h(Alert, { type: 'error', message: error, onDismiss: () => setError(null) }),
    
    h('p', { class: 'modal-description' }, 
      'Create a new household and become its owner. You can invite others using a join code.'
    ),
    
    h(FormInput, {
      label: 'Household Name',
      name: 'householdName',
      value: form.householdName,
      onChange: setField,
      placeholder: 'e.g., Smith Family',
      required: true
    })
  );
}

// ============================================================================
// Join Household Modal
// ============================================================================

function JoinHouseholdModal({ isOpen, onClose }) {
  const [mode, setMode] = useState('code'); // 'code' or 'request'
  const [joinCode, setJoinCode] = useState('');
  const [householdName, setHouseholdName] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleJoinWithCode = async () => {
    if (!joinCode.trim()) {
      setError('Join code is required');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/household/join/code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: joinCode.trim() })
      });

      const result = await response.json();

      if (result.success) {
        setSuccess(result.message);
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        setError(result.error || 'Failed to join household');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestToJoin = async () => {
    if (!householdName.trim()) {
      setError('Household name is required');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/household/join/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          householdName: householdName.trim(),
          message: message.trim()
        })
      });

      const result = await response.json();

      if (result.success) {
        setSuccess(result.message);
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        setError(result.error || 'Failed to send request');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setJoinCode('');
    setHouseholdName('');
    setMessage('');
    setError(null);
    setSuccess(null);
    setMode('code');
    onClose();
  };

  return h(Modal, {
    isOpen,
    onClose: handleClose,
    title: 'Join a Household',
    size: 'md',
    footer: success ? [] : [
      h(Button, { text: 'Cancel', variant: 'secondary', onClick: handleClose }),
      mode === 'code' 
        ? h(Button, { text: 'Join', variant: 'primary', onClick: handleJoinWithCode, loading })
        : h(Button, { text: 'Send Request', variant: 'primary', onClick: handleRequestToJoin, loading })
    ]
  },
    h(Alert, { type: 'error', message: error, onDismiss: () => setError(null) }),
    h(Alert, { type: 'success', message: success }),
    
    // Mode selector
    !success ? h('div', { class: 'mode-tabs' },
      h('button', {
        type: 'button',
        class: `mode-tab ${mode === 'code' ? 'active' : ''}`,
        onclick: () => setMode('code')
      }, 'Use Join Code'),
      h('button', {
        type: 'button',
        class: `mode-tab ${mode === 'request' ? 'active' : ''}`,
        onclick: () => setMode('request')
      }, 'Request to Join')
    ) : null,
    
    !success ? (
      mode === 'code' ? [
        h('p', { class: 'modal-description' }, 
          'Enter the join code provided by the household owner to join instantly.'
        ),
        h(FormInput, {
          label: 'Join Code',
          name: 'joinCode',
          value: joinCode,
          onChange: (val) => setJoinCode(val),
          placeholder: 'e.g., ABC123XY'
        })
      ] : [
        h('p', { class: 'modal-description' }, 
          'Send a request to join a household. The owner will need to approve your request.'
        ),
        h(FormInput, {
          label: 'Household Name',
          name: 'householdName',
          value: householdName,
          onChange: (val) => setHouseholdName(val),
          placeholder: 'Enter exact household name'
        }),
        h(FormTextarea, {
          label: 'Message (optional)',
          name: 'message',
          value: message,
          onChange: (val) => setMessage(val),
          placeholder: 'Introduce yourself...',
          rows: 3
        })
      ]
    ) : null
  );
}

// ============================================================================
// Join Code Display Modal (for Owners)
// ============================================================================

function JoinCodeModal({ isOpen, onClose, household }) {
  const [joinCode, setJoinCode] = useState(household?.joinCode || '');
  const [enabled, setEnabled] = useState(household?.joinCodeEnabled || false);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (household) {
      setJoinCode(household.joinCode || '');
      setEnabled(household.joinCodeEnabled || false);
    }
  }, [household]);

  const handleGenerateCode = async () => {
    setLoading(true);
    try {
      const response = await fetch('/settings/household/joincode/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();

      if (result.success) {
        setJoinCode(result.joinCode);
        setEnabled(result.enabled);
      }
    } catch (err) {
      console.error('Failed to generate code:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async () => {
    setLoading(true);
    try {
      const response = await fetch('/settings/household/joincode/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !enabled })
      });

      const result = await response.json();

      if (result.success) {
        setEnabled(result.enabled);
      }
    } catch (err) {
      console.error('Failed to toggle code:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(joinCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return h(Modal, {
    isOpen,
    onClose,
    title: 'Manage Join Code',
    size: 'sm',
    footer: [
      h(Button, { text: 'Close', variant: 'secondary', onClick: onClose })
    ]
  },
    h('p', { class: 'modal-description' }, 
      'Share this code with others to let them join your household instantly.'
    ),
    
    h('div', { class: 'join-code-display' },
      joinCode 
        ? h('div', { class: 'code-box' },
            h('span', { class: 'code-text' }, joinCode),
            h('button', { 
              type: 'button',
              class: 'copy-btn',
              onclick: handleCopy
            }, copied ? 'Copied!' : 'Copy')
          )
        : h('p', { class: 'no-code' }, 'No join code generated yet')
    ),
    
    h('div', { class: 'join-code-actions' },
      h('button', {
        type: 'button',
        class: 'btn-secondary',
        onclick: handleGenerateCode,
        disabled: loading
      }, loading ? 'Generating...' : (joinCode ? 'Regenerate Code' : 'Generate Code')),
      
      joinCode ? h('label', { class: 'toggle-label' },
        h('input', {
          type: 'checkbox',
          checked: enabled,
          onchange: handleToggle,
          disabled: loading
        }),
        h('span', null, enabled ? 'Code Enabled' : 'Code Disabled')
      ) : null
    ),
    
    !enabled && joinCode ? h('p', { class: 'warning-text' }, 
      'The join code is currently disabled. Enable it to allow new members to join.'
    ) : null
  );
}

// ============================================================================
// Pending Requests Modal (for Owners)
// ============================================================================

function PendingRequestsModal({ isOpen, onClose, household, onUpdate }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && household) {
      loadRequests();
    }
  }, [isOpen, household]);

  const loadRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/settings/household/requests');
      const result = await response.json();

      if (result.success) {
        setRequests(result.requests);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to load requests');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (requestId) => {
    try {
      const response = await fetch(`/settings/household/requests/${requestId}/accept`, {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        setRequests(prev => prev.filter(r => r.id !== requestId));
        if (onUpdate) onUpdate();
      }
    } catch (err) {
      console.error('Failed to accept request:', err);
    }
  };

  const handleDeny = async (requestId) => {
    try {
      const response = await fetch(`/settings/household/requests/${requestId}/deny`, {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        setRequests(prev => prev.filter(r => r.id !== requestId));
        if (onUpdate) onUpdate();
      }
    } catch (err) {
      console.error('Failed to deny request:', err);
    }
  };

  return h(Modal, {
    isOpen,
    onClose,
    title: 'Pending Join Requests',
    size: 'md',
    footer: [
      h(Button, { text: 'Close', variant: 'secondary', onClick: onClose })
    ]
  },
    h(Alert, { type: 'error', message: error }),
    
    loading 
      ? h('p', { class: 'loading-text' }, 'Loading requests...')
      : requests.length === 0 
        ? h('p', { class: 'empty-text' }, 'No pending requests')
        : h('div', { class: 'requests-list' },
            ...requests.map(req =>
              h('div', { class: 'request-card' },
                h('div', { class: 'request-info' },
                  h('strong', null, req.username),
                  req.firstName || req.lastName 
                    ? h('span', { class: 'request-name' }, ` (${req.firstName} ${req.lastName})`.trim())
                    : null,
                  req.email ? h('div', { class: 'request-email' }, req.email) : null,
                  req.message ? h('div', { class: 'request-message' }, `"${req.message}"`) : null
                ),
                h('div', { class: 'request-actions' },
                  h('button', {
                    type: 'button',
                    class: 'btn-accept',
                    onclick: () => handleAccept(req.id)
                  }, 'Accept'),
                  h('button', {
                    type: 'button',
                    class: 'btn-deny',
                    onclick: () => handleDeny(req.id)
                  }, 'Deny')
                )
              )
            )
          )
  );
}

// ============================================================================
// Household Card Component
// ============================================================================

function HouseholdCard({ household, isActive, onManageCode, onViewRequests }) {
  const handleSwitch = () => {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/switch_household/${household.id}`;
    document.body.appendChild(form);
    form.submit();
  };

  return h('div', { class: `household-card ${isActive ? 'active' : ''}` },
    h('div', { class: 'household-card-header' },
      h('div', { class: 'household-card-title' },
        h('strong', null, household.name),
        isActive ? h('span', { class: 'active-badge' }, 'Active') : null
      ),
      h('span', { class: 'role-tag' }, household.role)
    ),
    
    h('div', { class: 'household-card-actions' },
      !isActive 
        ? h('button', {
            type: 'button',
            class: 'btn-switch',
            onclick: handleSwitch
          }, 'Switch to')
        : null,
      
      household.role === 'Owner' ? [
        h('button', {
          type: 'button',
          class: 'btn-manage-code',
          onclick: () => onManageCode(household)
        }, 'Join Code'),
        
        h('button', {
          type: 'button',
          class: `btn-requests ${household.pendingRequests > 0 ? 'has-requests' : ''}`,
          onclick: () => onViewRequests(household)
        }, 
          household.pendingRequests > 0 
            ? `Requests (${household.pendingRequests})`
            : 'Requests'
        ),
        
        h('a', {
          href: '/household/settings',
          class: 'btn-settings'
        }, 'Settings')
      ] : null
    )
  );
}

// ============================================================================
// Pending User Request Card
// ============================================================================

function UserPendingRequestCard({ request, onCancel }) {
  return h('div', { class: 'pending-request-card' },
    h('div', { class: 'pending-request-info' },
      h('span', null, 'Request to join: '),
      h('strong', null, request.householdName)
    ),
    h('button', {
      type: 'button',
      class: 'btn-cancel-request',
      onclick: () => onCancel(request.id)
    }, 'Cancel')
  );
}

// ============================================================================
// Main Container
// ============================================================================

function ManageHouseholdsContainer({ households = [], pendingRequests = [], currentHouseholdId = null }) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [showRequestsModal, setShowRequestsModal] = useState(false);
  const [selectedHousehold, setSelectedHousehold] = useState(null);
  const [userPendingRequests, setUserPendingRequests] = useState(pendingRequests);

  const handleManageCode = (household) => {
    setSelectedHousehold(household);
    setShowCodeModal(true);
  };

  const handleViewRequests = (household) => {
    setSelectedHousehold(household);
    setShowRequestsModal(true);
  };

  const handleCancelRequest = async (requestId) => {
    try {
      const response = await fetch(`/household/requests/${requestId}/cancel`, {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        setUserPendingRequests(prev => prev.filter(r => r.id !== requestId));
      }
    } catch (err) {
      console.error('Failed to cancel request:', err);
    }
  };

  return h('div', { class: 'manage-households-container' },
    // Header with action buttons
    h('div', { class: 'manage-header' },
      h('div', { class: 'action-buttons' },
        h('button', {
          type: 'button',
          class: 'btn-primary btn-create',
          onclick: () => setShowCreateModal(true)
        }, '+ Create Household'),
        h('button', {
          type: 'button',
          class: 'btn-secondary btn-join',
          onclick: () => setShowJoinModal(true)
        }, 'Join Household')
      )
    ),
    
    // Households list
    households.length > 0
      ? h('div', { class: 'households-section' },
          h('h2', null, 'Your Households'),
          h('div', { class: 'households-grid' },
            ...households.map(hh =>
              h(HouseholdCard, {
                household: hh,
                isActive: hh.id === currentHouseholdId,
                onManageCode: handleManageCode,
                onViewRequests: handleViewRequests
              })
            )
          )
        )
      : h('div', { class: 'empty-state' },
          h('h3', null, 'No Households Yet'),
          h('p', null, 'Create your own household or join an existing one to get started.')
        ),
    
    // User's pending requests
    userPendingRequests.length > 0
      ? h('div', { class: 'pending-section' },
          h('h3', null, 'Your Pending Requests'),
          h('div', { class: 'pending-requests-list' },
            ...userPendingRequests.map(req =>
              h(UserPendingRequestCard, {
                request: req,
                onCancel: handleCancelRequest
              })
            )
          )
        )
      : null,
    
    // Modals
    h(CreateHouseholdModal, {
      isOpen: showCreateModal,
      onClose: () => setShowCreateModal(false)
    }),
    
    h(JoinHouseholdModal, {
      isOpen: showJoinModal,
      onClose: () => setShowJoinModal(false)
    }),
    
    h(JoinCodeModal, {
      isOpen: showCodeModal,
      onClose: () => setShowCodeModal(false),
      household: selectedHousehold
    }),
    
    h(PendingRequestsModal, {
      isOpen: showRequestsModal,
      onClose: () => setShowRequestsModal(false),
      household: selectedHousehold,
      onUpdate: () => window.location.reload()
    })
  );
}

// ============================================================================
// Initialize
// ============================================================================

export function initManageHouseholds(containerId, data) {
  const container = document.getElementById(containerId);
  if (container && data) {
    render(
      h(ManageHouseholdsContainer, {
        households: data.households || [],
        pendingRequests: data.pendingRequests || [],
        currentHouseholdId: data.currentHouseholdId
      }),
      container
    );
  }
}


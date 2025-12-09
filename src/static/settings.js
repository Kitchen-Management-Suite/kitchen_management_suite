/**
 * settings.js
 * Settings page component using hook.js and components.js
 */

import { h, useState, render } from './hook.js';
import { FormInput, FormRow, Button, Alert, useForm } from './components.js';

/* SettingsSection - reusable section container */
function SettingsSection(props) {
  const { title, children, variant = '' } = props;
  const childArray = children == null ? [] : (Array.isArray(children) ? children : [children]);
  
  return h('section', { class: `settings-section${variant ? ' ' + variant : ''}` },
    h('h2', null, title),
    h('div', { class: 'settings-content' },
      ...childArray
    )
  );
}

/* ProfileForm - handles profile updates */
function ProfileForm(props) {
  const { initialData = {} } = props;
  const [formData, setField] = useForm({
    first_name: initialData.firstName || '',
    last_name: initialData.lastName || '',
    height: initialData.height || '',
    weight: initialData.weight || '',
    calorie_goal: initialData.calorieGoal || '',
    dietary_preferences: initialData.dietaryPreferences || '',
    allergies: initialData.allergies || ''
  });

  return h('form', { 
    method: 'POST', 
    action: '/settings/profile/update',
    class: 'settings-form'
  },
    h(FormRow, null,
      h(FormInput, {
        label: 'First Name',
        name: 'first_name',
        value: formData.first_name,
        onChange: setField,
        placeholder: 'Enter first name'
      }),
      h(FormInput, {
        label: 'Last Name',
        name: 'last_name',
        value: formData.last_name,
        onChange: setField,
        placeholder: 'Enter last name'
      })
    ),
    h(FormRow, null,
      h(FormInput, {
        label: 'Height (cm)',
        name: 'height',
        type: 'number',
        value: formData.height,
        onChange: setField,
        min: 0,
        step: 0.1
      }),
      h(FormInput, {
        label: 'Weight (kg)',
        name: 'weight',
        type: 'number',
        value: formData.weight,
        onChange: setField,
        min: 0,
        step: 0.1
      })
    ),
    h(FormInput, {
      label: 'Calorie Goal',
      name: 'calorie_goal',
      type: 'number',
      value: formData.calorie_goal,
      onChange: setField,
      min: 0
    }),
    h(FormInput, {
      label: 'Dietary Preferences',
      name: 'dietary_preferences',
      value: formData.dietary_preferences,
      onChange: setField,
      placeholder: 'e.g., vegetarian, low-carb'
    }),
    h(FormInput, {
      label: 'Allergies',
      name: 'allergies',
      value: formData.allergies,
      onChange: setField,
      placeholder: 'e.g., peanuts, shellfish'
    }),
    h(Button, { text: 'Update Profile', type: 'submit' })
  );
}

/* AccountForm - handles account updates */
function AccountForm(props) {
  const { initialData = {} } = props;
  const [formData, setField] = useForm({
    username: initialData.username || '',
    email: initialData.email || ''
  });

  return h('form', { 
    method: 'POST', 
    action: '/settings/account/update',
    class: 'settings-form'
  },
    h(FormInput, {
      label: 'Username',
      name: 'username',
      value: formData.username,
      onChange: setField,
      required: true
    }),
    h(FormInput, {
      label: 'Email',
      name: 'email',
      type: 'email',
      value: formData.email,
      onChange: setField,
      required: true
    }),
    h('div', { class: 'form-group' },
      h('label', null, 'Date of Birth'),
      h('input', {
        type: 'text',
        class: 'form-input',
        value: initialData.dateOfBirth || 'Not set',
        disabled: true
      }),
      h('small', { class: 'form-hint' }, 'Date of birth cannot be changed')
    ),
    h(Button, { text: 'Update Account', type: 'submit' })
  );
}

/* PasswordForm - handles password changes */
function PasswordForm() {
  const [formData, setField, reset] = useForm({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  return h('form', { 
    method: 'POST', 
    action: '/settings/password/change',
    class: 'settings-form'
  },
    h(FormInput, {
      label: 'Current Password',
      name: 'current_password',
      type: 'password',
      value: formData.current_password,
      onChange: setField,
      required: true
    }),
    h(FormInput, {
      label: 'New Password',
      name: 'new_password',
      type: 'password',
      value: formData.new_password,
      onChange: setField,
      required: true
    }),
    h(FormInput, {
      label: 'Confirm Password',
      name: 'confirm_password',
      type: 'password',
      value: formData.confirm_password,
      onChange: setField,
      required: true
    }),
    h(Button, { text: 'Change Password', type: 'submit' })
  );
}

/* HouseholdList - displays households with leave option */
function HouseholdList(props) {
  const { households = [] } = props;

  if (households.length === 0) {
    return h('p', { class: 'empty-message' }, 'You are not a member of any households.');
  }

  return h('form', { 
    method: 'POST', 
    action: '/settings/household/leave',
    class: 'settings-form'
  },
    h('div', { class: 'form-group' },
      h('label', { for: 'household_id' }, 'Select Household to Leave'),
      h('select', {
        name: 'household_id',
        id: 'household_id',
        class: 'form-select',
        required: true
      },
        h('option', { value: '' }, 'Choose household...'),
        ...households.map(hh =>
          h('option', { value: hh.HouseholdID },
            `${hh.HouseholdName} (${hh.Role})`
          )
        )
      )
    ),
    h(Button, { text: 'Leave Household', type: 'submit', variant: 'secondary' })
  );
}

/* DeleteAccountForm - handles account deletion */
function DeleteAccountForm() {
  const [confirmText, setConfirmText] = useState('');

  return h('form', { 
    method: 'POST', 
    action: '/settings/account/delete',
    class: 'settings-form'
  },
    h('div', { class: 'warning-box' },
      h('p', null, 'This action is permanent and cannot be undone.'),
      h('p', null, 'All your data including profile, recipes, and household memberships will be deleted.')
    ),
    h('div', { class: 'form-group' },
      h('label', { for: 'confirm_delete' }, 'Type DELETE to confirm'),
      h('input', {
        type: 'text',
        name: 'confirm_delete',
        id: 'confirm_delete',
        class: 'form-input',
        value: confirmText,
        oninput: (e) => setConfirmText(e.target.value),
        placeholder: 'DELETE',
        required: true
      })
    ),
    h(Button, { 
      text: 'Delete Account', 
      type: 'submit', 
      variant: 'danger',
      disabled: confirmText !== 'DELETE'
    })
  );
}

/* ExportDataForm - handles data export */
function ExportDataForm() {
  return h('form', { 
    method: 'POST', 
    action: '/settings/data/export',
    class: 'settings-form'
  },
    h('p', null, 'Download all your account and profile data as JSON.'),
    h(Button, { text: 'Export My Data', type: 'submit', variant: 'secondary' })
  );
}

/* Main Settings Container */
export function SettingsContainer(props) {
  const { userData = {}, profileData = {}, households = [] } = props;

  return h('div', { class: 'settings-container' },
    h('h1', null, 'Settings'),

    h(SettingsSection, { title: 'Profile' },
      h(ProfileForm, { initialData: { ...userData, ...profileData } })
    ),

    h(SettingsSection, { title: 'Account' },
      h(AccountForm, { initialData: userData }),
      h('div', { class: 'settings-divider' }),
      h('h3', null, 'Change Password'),
      h(PasswordForm)
    ),

    h(SettingsSection, { title: 'Households' },
      h(HouseholdList, { households })
    ),

    h(SettingsSection, { title: 'Privacy & Data' },
      h('p', null, 'Your data is stored securely and used only to operate Kitchen Management Suite.'),
      h(ExportDataForm)
    ),

    h(SettingsSection, { title: 'Danger Zone', variant: 'danger-section' },
      h(DeleteAccountForm)
    )
  );
}

/* Initialize settings page */
export function initSettings(containerId, data) {
  const container = document.getElementById(containerId);
  if (container && data) {
    render(
      h(SettingsContainer, {
        userData: data.userData,
        profileData: data.profileData,
        households: data.households
      }),
      container
    );
  }
}
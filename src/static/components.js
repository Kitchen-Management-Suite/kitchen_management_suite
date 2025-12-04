/**
 * components.js
 * Reusable UI components built on hook.js
 * Provides Modal, form helpers, lists, and common UI patterns
 */

import { h, useState, useEffect } from './hook.js';

/**
 * Flatten nested arrays of children recursively
 * Filters out null/undefined/false values
 */
function flattenChildren(children) {
  if (children == null || children === false) return [];
  if (!Array.isArray(children)) return [children];
  
  const result = [];
  for (const child of children) {
    if (child == null || child === false) continue;
    if (Array.isArray(child)) {
      result.push(...flattenChildren(child));
    } else {
      result.push(child);
    }
  }
  return result;
}

/* Modal
 * handles escape key, backdrop clicks, and structured layout
 */
export function Modal(props) {
  const { 
    isOpen = false, 
    onClose, 
    title = '', 
    size = 'md',
    children,
    footer = null
  } = props;

  // Flatten children to handle nested arrays from ternary operators
  const childArray = flattenChildren(children);
  const footerArray = flattenChildren(footer);

  useEffect(() => {
    if (!isOpen) return;
    
    const handleEscape = (e) => {
      if (e.key === 'Escape' && onClose) onClose();
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // close when clicking backdrop
  const handleBackdropClick = (e) => {
    if (e.target.classList.contains('modal') && onClose) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return h('div', { 
    class: 'modal active', 
    onclick: handleBackdropClick 
  },
    h('div', { class: `modal-content modal-${size}` },
      h('div', { class: 'modal-header' },
        h('h3', null, title),
        h('button', { 
          class: 'modal-close', 
          type: 'button',
          onclick: onClose 
        }, '×')
      ),
      // body section
      h('div', { class: 'modal-body' }, ...childArray),
      // optional footer
      footerArray.length > 0 
        ? h('div', { class: 'modal-footer' }, ...footerArray) 
        : null
    )
  );
}

/* FormInput - generic labeled input field
 * supports validation states and required markers
 */
export function FormInput(props) {
  const { 
    label, 
    name, 
    type = 'text', 
    value = '', 
    onChange,
    placeholder = '',
    required = false,
    min,
    max,
    step,
    error = null
  } = props;

  return h('div', { class: 'form-group' },
    label ? h('label', { for: name }, label, required ? ' *' : '') : null,
    h('input', {
      type,
      name,
      id: name,
      class: `form-input${error ? ' input-error' : ''}`,
      value,
      placeholder,
      required: required || undefined,
      min: min !== undefined ? min : undefined,
      max: max !== undefined ? max : undefined,
      step: step !== undefined ? step : undefined,
      oninput: (e) => onChange && onChange(e.target.value, name)
    }),
    error ? h('div', { class: 'validation-error' }, error) : null
  );
}

/* FormSelect - simple dropdown select
 * renders options and controlled value
 */
export function FormSelect(props) {
  const { 
    label, 
    name, 
    value = '', 
    onChange,
    options = [],
    required = false 
  } = props;

  return h('div', { class: 'form-group' },
    label ? h('label', { for: name }, label, required ? ' *' : '') : null,
    h('select', {
      name,
      id: name,
      class: 'form-select',
      value,
      onchange: (e) => onChange && onChange(e.target.value, name)
    },
      ...options.map(opt => 
        h('option', { 
          value: opt.value,
          selected: opt.value === value ? true : undefined
        }, opt.text || opt.value)
      )
    )
  );
}

/* FormTextarea - textarea with optional label */
export function FormTextarea(props) {
  const { 
    label, 
    name, 
    value = '', 
    onChange,
    placeholder = '',
    rows = 3,
    required = false 
  } = props;

  return h('div', { class: 'form-group' },
    label ? h('label', { for: name }, label, required ? ' *' : '') : null,
    h('textarea', {
      name,
      id: name,
      class: 'form-textarea',
      rows,
      placeholder,
      value,
      required: required || undefined,
      oninput: (e) => onChange && onChange(e.target.value, name)
    })
  );
}

/* FormRow - layout wrapper for row-style grouping */
export function FormRow(props) {
  const { children = [] } = props;
  return h('div', { class: 'form-row' }, ...children);
}

/* FormSection - labeled container grouping related fields */
export function FormSection(props) {
  const { label, children = [], required = false } = props;
  return h('div', { class: 'form-section' },
    label ? h('label', null, label, required ? ' *' : '') : null,
    ...children
  );
}

/* DynamicList - add/remove list entries
 * renders inputs for adding and displays current items
 */
export function DynamicList(props) {
  const {
    label,
    items = [],
    onAdd,
    onRemove,
    renderItem,
    renderInputs,
    addButtonText = 'Add',
    numbered = false
  } = props;

  return h('div', { class: 'form-section' },
    label ? h('label', null, label) : null,
    
    // input area for adding new entries
    h('div', { class: 'input-group' },
      renderInputs ? renderInputs() : null,
      h('button', {
        type: 'button',
        class: 'btn-primary btn-sm',
        onclick: onAdd
      }, addButtonText)
    ),
    
    // current list items
    h('div', { class: 'list-container' },
      ...items.map((item, index) =>
        h('div', { class: 'list-item' },
          numbered ? h('span', { class: 'list-item-number' }, `${index + 1}.`) : null,
          h('div', { class: 'list-item-content' },
            renderItem ? renderItem(item, index) : String(item)
          ),
          h('button', {
            type: 'button',
            class: 'btn-remove',
            onclick: () => onRemove && onRemove(index)
          }, '×')
        )
      )
    )
  );
}

/* CheckboxGroup - multi-select checkbox list
 * supports optional "select all" controls
 */
export function CheckboxGroup(props) {
  const {
    label,
    options = [],
    selected = [],
    onChange,
    showSelectAll = false
  } = props;

  // toggle a single checkbox
  const handleToggle = (value) => {
    const newSelected = selected.includes(value)
      ? selected.filter(v => v !== value)
      : [...selected, value];
    onChange && onChange(newSelected);
  };

  const selectAll = () => onChange && onChange(options.map(o => o.value));
  const clearAll = () => onChange && onChange([]);

  return h('div', { class: 'form-section' },
    h('div', { class: 'form-section-header' },
      label ? h('label', null, label) : null,
      showSelectAll ? h('div', { class: 'checkbox-actions' },
        h('button', { type: 'button', class: 'btn-sm', onclick: selectAll }, 'Select All'),
        h('button', { type: 'button', class: 'btn-sm', onclick: clearAll }, 'Clear')
      ) : null
    ),
    h('div', { class: 'checkbox-group' },
      ...options.map(opt =>
        h('label', { class: 'checkbox-label' },
          h('input', {
            type: 'checkbox',
            value: opt.value,
            checked: selected.includes(opt.value) ? true : undefined,
            onchange: () => handleToggle(opt.value)
          }),
          h('span', null, opt.text || opt.value)
        )
      )
    )
  );
}

/* Alert - dismissible alert banner */
export function Alert(props) {
  const { type = 'info', message, onDismiss } = props;
  
  if (!message) return null;
  
  return h('div', { class: `alert alert-${type}` },
    h('span', null, message),
    onDismiss ? h('button', {
      type: 'button',
      class: 'alert-dismiss',
      onclick: onDismiss
    }, '×') : null
  );
}

/* Button - supports variants, disabled, loading states */
export function Button(props) {
  const { 
    text, 
    onClick, 
    type = 'button', 
    variant = 'primary',
    disabled = false,
    loading = false
  } = props;

  return h('button', {
    type,
    class: `btn-${variant}`,
    onclick: onClick,
    disabled: disabled || loading || undefined
  }, loading ? 'Loading...' : text);
}

/* useForm - simple object-based form state helper
 * returns: [data, setField, reset, setData]
 */
export function useForm(initialValues = {}) {
  const [data, setData] = useState({ ...initialValues });
  
  const setField = (value, name) => {
    setData(prev => ({ ...prev, [name]: value }));
  };
  
  const reset = () => setData({ ...initialValues });
  
  return [data, setField, reset, setData];
}

/* useList - minimal list add/remove utility
 * returns: [items, add, remove, clear, setItems]
 */
export function useList(initialItems = []) {
  const [items, setItems] = useState([...initialItems]);
  
  const addItem = (item) => setItems(prev => [...prev, item]);
  const removeItem = (index) => setItems(prev => prev.filter((_, i) => i !== index));
  const clearItems = () => setItems([]);
  
  return [items, addItem, removeItem, clearItems, setItems];
}

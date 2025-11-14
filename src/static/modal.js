  /**
   * modal.js
   * allows for the building of complex modal forms
   * had to create because hook.js does not handle modals well
   */


  /*
   TO DO:
    Need to go through and make sure specific form things are editable
     for example, with a recipes form, the instructions should be editable textareas
     right now they are static, and the only way to change them is to delete and re-add
     at the very least should look into adding a reorder system.
  */

  export class BuildModal {
    constructor(config) {
      this.config = config;
      this.modal = null;
      this.data = {};
    }

    show() {
      const modal = document.createElement('div');
      modal.className = 'modal active';
      modal.id = this.config.id || `modal-${Date.now()}`;
      
      modal.innerHTML = `
        <div class="modal-content modal-${this.config.size || 'md'}">
          <div class="modal-header">
            <h3>${this.config.title}</h3>
            <button class="modal-close" type="button">×</button>
          </div>
          <div class="modal-body">
            ${this.buildForm()}
          </div>
          <div class="modal-footer">
            ${this.buildFooter()}
          </div>
        </div>
      `;

      document.body.appendChild(modal);
      this.modal = modal;

      this.setupCloseHandlers();
      this.setupFieldHandlers();
      this.setupListHandlers();
      
      if (this.config.onOpen) this.config.onOpen(this);
      
      return this;
    }

    buildForm() {
      let html = '<form>';
      
      html += '<div class="alert alert-error" id="modal-alert"></div>';
      
      // Build each field
      this.config.fields.forEach(field => {
        if (field.type === 'text' || field.type === 'number') {
          html += this.buildInput(field);
        } else if (field.type === 'textarea') {
          html += this.buildTextarea(field);
        } else if (field.type === 'select') {
          html += this.buildSelect(field);
        } else if (field.type === 'row') {
          html += this.buildRow(field);
        } else if (field.type === 'checkboxes') {
          html += this.buildCheckboxGroup(field);
        } else if (field.type === 'list') {
          html += this.buildList(field);
        }
      });
      
      html += '</form>';
      return html;
    }

    buildInput(field) {
      return `
        <div class="form-section">
          <label>${field.label}${field.required ? ' *' : ''}</label>
          <input 
            type="${field.type}" 
            name="${field.name}" 
            id="${field.id || field.name}"
            class="form-input" 
            placeholder="${field.placeholder || ''}"
            ${field.required ? 'required' : ''}
            ${field.min ? `min="${field.min}"` : ''}
            ${field.max ? `max="${field.max}"` : ''}
          >
        </div>
      `;
    }

    buildTextarea(field) {
      return `
        <div class="form-section">
          <label>${field.label}${field.required ? ' *' : ''}</label>
          <textarea 
            name="${field.name}" 
            id="${field.id || field.name}"
            class="form-textarea" 
            placeholder="${field.placeholder || ''}"
            rows="${field.rows || 3}"
            ${field.required ? 'required' : ''}
          ></textarea>
        </div>
      `;
    }

    buildSelect(field) {
      const options = field.options.map(opt => 
        `<option value="${opt.value}" ${opt.selected ? 'selected' : ''}>${opt.text}</option>`
      ).join('');
      
      return `
        <div class="form-section">
          <label>${field.label}${field.required ? ' *' : ''}</label>
          <select name="${field.name}" id="${field.id || field.name}" class="form-select">
            ${options}
          </select>
        </div>
      `;
    }

    buildRow(field) {
      const groups = field.groups.map(group => {
        let input = '';
        if (group.type === 'select') {
          const options = group.options.map(opt => 
            `<option value="${opt.value}" ${opt.selected ? 'selected' : ''}>${opt.text}</option>`
          ).join('');
          input = `<select name="${group.name}" class="form-select">${options}</select>`;
        } else {
          input = `
            <input 
              type="${group.type || 'text'}" 
              name="${group.name}" 
              class="form-input" 
              placeholder="${group.placeholder || ''}"
              ${group.min ? `min="${group.min}"` : ''}
            >
          `;
        }
        
        return `
          <div class="form-group">
            <label>${group.label}</label>
            ${input}
          </div>
        `;
      }).join('');
      
      return `<div class="form-row">${groups}</div>`;
    }

    buildCheckboxGroup(field) {
      return `
        <div class="form-section">
          <div class="form-section-header">
            <label>${field.label}${field.required ? ' *' : ''}</label>
            ${field.showSelectAll ? `
              <div style="display: flex; gap: 0.5rem;">
                <button type="button" class="btn-sm" data-action="select-all" data-target="${field.id}">Select All</button>
                <button type="button" class="btn-sm" data-action="clear-all" data-target="${field.id}">Clear</button>
              </div>
            ` : ''}
          </div>
          <div class="checkbox-group" id="${field.id}"></div>
        </div>
      `;
    }

  buildList(field) {
    const inputHTML = field.inputs.map(input => {
      if (input.type === 'select') {
        const options = input.options.map(opt => 
          `<option value="${opt}">${opt}</option>`
        ).join('');
        return `<select class="form-select" id="${input.id}" style="flex: ${input.flex || 1};">${options}</select>`;
      } else if (input.type === 'textarea') {
        return `<textarea class="form-textarea" id="${input.id}" placeholder="${input.placeholder}" rows="2"></textarea>`;
      } else if (input.type === 'number') {
        return `<input 
          type="number" 
          class="form-input" 
          id="${input.id}" 
          placeholder="${input.placeholder}" 
          style="flex: ${input.flex || 1};"
          ${input.min !== undefined ? `min="${input.min}"` : ''}
          ${input.max !== undefined ? `max="${input.max}"` : ''}
          ${input.step !== undefined ? `step="${input.step}"` : ''}
        >`;
      } else {
        return `<input 
          type="text" 
          class="form-input" 
          id="${input.id}" 
          placeholder="${input.placeholder}" 
          style="flex: ${input.flex || 1};"
        >`;
      }
    }).join('');
    
    return `
      <div class="form-section">
        <label>${field.label}${field.required ? ' *' : ''}</label>
        <div class="input-group">
          ${inputHTML}
          <button type="button" class="btn-primary" data-action="add-list-item" data-list="${field.id}">${field.addButtonText || 'Add'}</button>
        </div>
        <div id="${field.id}"></div>
      </div>
    `;
  }

    buildFooter() {
      return this.config.buttons.map(btn => {
        const isPrimary = btn.primary;
        return `
          <button 
            type="button" 
            class="${isPrimary ? 'btn-primary' : 'btn-secondary'}" 
            data-action="${btn.action}"
          >
            ${btn.text}
          </button>
        `;
      }).join('');
    }

    setupCloseHandlers() {
      const closeBtn = this.modal.querySelector('.modal-close');
      closeBtn.onclick = () => this.close();
      
      this.modal.onclick = (e) => {
        if (e.target === this.modal) this.close();
      };
    }

    setupFieldHandlers() {
      // Checkbox select all/clear
      this.modal.querySelectorAll('[data-action="select-all"]').forEach(btn => {
        btn.onclick = () => {
          const target = btn.dataset.target;
          this.modal.querySelectorAll(`#${target} input[type="checkbox"]`).forEach(cb => cb.checked = true);
        };
      });
      
      this.modal.querySelectorAll('[data-action="clear-all"]').forEach(btn => {
        btn.onclick = () => {
          const target = btn.dataset.target;
          this.modal.querySelectorAll(`#${target} input[type="checkbox"]`).forEach(cb => cb.checked = false);
        };
      });
    }

  setupListHandlers() {
    this.modal.querySelectorAll('[data-action="add-list-item"]').forEach(btn => {
      btn.onclick = () => {
        const listId = btn.dataset.list;
        const field = this.config.fields.find(f => f.id === listId);
        if (!field) return;
        
        // Get input values
        const values = {};
        field.inputs.forEach(input => {
          const el = this.modal.querySelector(`#${input.id}`);
          values[input.id] = el.value.trim();
        });
        
        // Validate inputs
        const validation = this.validateListInputs(field, values);
        if (!validation.valid) {
          this.showError(validation.error);
          const firstInput = this.modal.querySelector(`#${field.inputs[0].id}`);
          if (firstInput) firstInput.focus();
          return;
        }
        
        this.hideError();
        
        // Add to list
        const container = this.modal.querySelector(`#${listId}`);
        const item = this.createListItem(field, values);
        container.appendChild(item);
        
        // Clear inputs
        field.inputs.forEach(input => {
          const el = this.modal.querySelector(`#${input.id}`);
          if (input.type === 'select') {
            el.selectedIndex = 0;
          } else {
            el.value = '';
          }
        });
        
        this.modal.querySelector(`#${field.inputs[0].id}`).focus();
      };
    });
    
    this.modal.querySelectorAll('.modal-footer button').forEach(btn => {
      btn.onclick = () => {
        const action = btn.dataset.action;
        if (action === 'cancel') {
          this.close();
        } else if (action === 'submit') {
          this.handleSubmit();
        } else if (this.config.onAction) {
          this.config.onAction(action, this);
        }
      };
    });
  }

  validateListInputs(field, values) {
    // Validate each input based on its configuration
    for (const input of field.inputs) {
      const value = values[input.id];
      
      // Check required
      if (input.required && (!value || value.trim() === '')) {
        return { valid: false, error: `${input.placeholder || 'This field'} is required` };
      }
      
      // Check type validation
      if (input.type === 'number' && value) {
        const num = parseFloat(value);
        if (isNaN(num)) {
          return { valid: false, error: `${input.placeholder || 'This field'} must be a number` };
        }
        if (input.min !== undefined && num < parseFloat(input.min)) {
          return { valid: false, error: `${input.placeholder || 'This field'} must be at least ${input.min}` };
        }
        if (input.max !== undefined && num > parseFloat(input.max)) {
          return { valid: false, error: `${input.placeholder || 'This field'} must be at most ${input.max}` };
        }
      }
      
      // Check pattern validation
      if (input.pattern && value) {
        const regex = new RegExp(input.pattern);
        if (!regex.test(value)) {
          return { valid: false, error: input.patternError || `${input.placeholder || 'This field'} has an invalid format` };
        }
      }
    }
    
    return { valid: true };
  }

  createListItem(field, values) {
    const item = document.createElement('div');
    item.className = 'list-item';
    
    if (field.itemType === 'numbered') {
      const container = this.modal.querySelector(`#${field.id}`);
      const number = container.children.length + 1;
      
      item.innerHTML = `
        <span class="list-item-number">${number}.</span>
        <div class="list-item-content">${values[field.inputs[0].id]}</div>
        <button type="button" class="btn-remove">×</button>
      `;
      
      item.setAttribute('data-text', values[field.inputs[0].id]);
      
      item.querySelector('.btn-remove').onclick = () => {
        item.remove();
        this.renumberList(field.id);
      };
    } else {
      const primary = values[field.inputs[0].id];
      const secondary = field.inputs.slice(1).map(input => values[input.id]).filter(v => v).join(' ');
      
      item.innerHTML = `
        <div class="list-item-content">
          <div class="list-item-primary">${primary}</div>
          ${secondary ? `<div class="list-item-secondary">${secondary}</div>` : ''}
        </div>
        <button type="button" class="btn-remove">×</button>
      `;
      
      // Store all values as data attributes
      field.inputs.forEach(input => {
        const attrName = input.id.replace(/-/g, '_');
        item.setAttribute(`data-${attrName}`, values[input.id]);
      });
      
      item.querySelector('.btn-remove').onclick = () => item.remove();
    }
    
    return item;
  }

    renumberList(listId) {
      const container = this.modal.querySelector(`#${listId}`);
      Array.from(container.children).forEach((child, idx) => {
        const num = child.querySelector('.list-item-number');
        if (num) num.textContent = `${idx + 1}.`;
      });
    }

    async handleSubmit() {
      this.hideError();
      
      if (this.config.onSubmit) {
        const formData = this.getFormData();
        const submitBtn = this.modal.querySelector('[data-action="submit"]');
        const originalText = submitBtn.textContent;
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        
        try {
          await this.config.onSubmit(formData, this);
        } catch (err) {
          console.error('Submit error:', err);
          this.showError(err.message || 'An error occurred');
        } finally {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
      }
    }

  getFormData() {
    const form = this.modal.querySelector('form');
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
      data[key] = value;
    }
    
    // Get list data
    this.config.fields.filter(f => f.type === 'list').forEach(field => {
      const items = this.modal.querySelectorAll(`#${field.id} .list-item`);
      data[field.id] = Array.from(items).map(item => {
        const itemData = {};
        field.inputs.forEach(input => {
          const attrName = input.id.replace(/-/g, '_');
          const dataKey = input.id.replace(/^new-/, '');
          itemData[dataKey] = item.getAttribute(`data-${attrName}`) || item.getAttribute('data-text');
        });
        return itemData;
      });
    });
    
    // Get checkbox data
    this.config.fields.filter(f => f.type === 'checkboxes').forEach(field => {
      const checked = this.modal.querySelectorAll(`#${field.id} input:checked`);
      data[field.id] = Array.from(checked).map(cb => parseInt(cb.value));
    });
    
    return data;
  }

    showError(message) {
      const alert = this.modal.querySelector('#modal-alert');
      if (alert) {
        alert.textContent = message;
        alert.classList.add('active');
        alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }

    hideError() {
      const alert = this.modal.querySelector('#modal-alert');
      if (alert) {
        alert.classList.remove('active');
      }
    }

    populateCheckboxes(fieldId, items, checkedIds = []) {
      const container = this.modal.querySelector(`#${fieldId}`);
      if (!container) return;
      
      container.innerHTML = '';
      
      items.forEach(item => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = item.id;
        checkbox.checked = checkedIds.includes(item.id);
        
        const span = document.createElement('span');
        span.textContent = item.name;
        
        label.appendChild(checkbox);
        label.appendChild(span);
        container.appendChild(label);
      });
    }

    close() {
      if (this.modal) {
        this.modal.remove();
        this.modal = null;
        if (this.config.onClose) this.config.onClose();
      }
    }
  }
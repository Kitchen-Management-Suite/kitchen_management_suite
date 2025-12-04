import { h, useState, render } from "./hook.js";
import { Modal, FormInput, FormSelect, Alert, Button, useForm } from './components.js';

const UNIT_OPTIONS = [
  { value: 'piece', text: 'piece' },
  { value: 'cup', text: 'cup' },
  { value: 'tbsp', text: 'tbsp' },
  { value: 'tsp', text: 'tsp' },
  { value: 'oz', text: 'oz' },
  { value: 'lb', text: 'lb' },
  { value: 'g', text: 'g' },
  { value: 'kg', text: 'kg' },
  { value: 'ml', text: 'ml' },
  { value: 'l', text: 'l' },
  { value: 'clove', text: 'clove' },
  { value: 'stick', text: 'stick' }
];

function AddItemModal({ isOpen, onClose }) {
  const [form, setField, resetForm] = useForm({
    itemName: '',
    quantity: '1',
    unit: 'piece'
  });
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  // Search for items from API
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }

    setSearching(true);
    setError(null);

    try {
      const response = await fetch('/pantry/search_items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery.trim(), page: 1, page_size: 10 })
      });

      const result = await response.json();

      if (result.success) {
        setSearchResults(result.products || []);
        if (result.products.length === 0) {
          setError('No items found. Try a different search term.');
        }
      } else {
        setError(result.error || 'Search failed');
      }
    } catch (err) {
      setError('Failed to search items');
    } finally {
      setSearching(false);
    }
  };

  // Select an item from search results
  const handleSelectItem = (product) => {
    setField(product.product_name || 'Unknown Item', 'itemName');
    setShowSearch(false);
    setSearchResults([]);
    setSearchQuery('');
  };

  // Submit the form to add item
  const handleSubmit = async () => {
    if (!form.itemName.trim()) {
      setError('Item name is required');
      return;
    }
    if (!form.quantity || parseFloat(form.quantity) <= 0) {
      setError('Valid quantity is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/pantry/add_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          itemName: form.itemName.trim(),
          quantity: parseFloat(form.quantity),
          unit: form.unit,
          source: 'custom'
        })
      });

      const result = await response.json();

      if (result.success) {
        handleClose();
        window.location.reload();
      } else {
        setError(result.error || 'Failed to add item');
      }
    } catch (err) {
      setError('An error occurred while adding the item');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    setError(null);
    setSearchQuery('');
    setSearchResults([]);
    setShowSearch(false);
    onClose();
  };

  return h(Modal, {
    isOpen,
    onClose: handleClose,
    title: 'Add Item to Pantry',
    size: 'md',
    footer: [
      h(Button, { text: 'Cancel', variant: 'secondary', onClick: handleClose }),
      h(Button, { text: 'Add Item', variant: 'primary', onClick: handleSubmit, loading, disabled: showSearch })
    ]
  },
    h(Alert, { type: 'error', message: error, onDismiss: () => setError(null) }),
    
    // Toggle between search and manual
    !showSearch ? [
      h(FormInput, {
        label: 'Item Name',
        name: 'itemName',
        value: form.itemName,
        onChange: setField,
        placeholder: 'Enter item name',
        required: true
      }),
      
      h('div', { class: 'form-section' },
        h('button', {
          type: 'button',
          class: 'btn-sm',
          onclick: () => setShowSearch(true),
          style: 'margin-bottom: 1rem;'
        }, '🔍 Search OpenFoodFacts')
      ),
      
      h('div', { class: 'form-row' },
        h(FormInput, {
          label: 'Quantity',
          name: 'quantity',
          type: 'number',
          value: form.quantity,
          onChange: setField,
          placeholder: '1',
          min: 0.01,
          step: 0.01,
          required: true
        }),
        h(FormSelect, {
          label: 'Unit',
          name: 'unit',
          value: form.unit,
          onChange: setField,
          options: UNIT_OPTIONS,
          required: true
        })
      )
    ] : [
      // Search interface
      h('div', { class: 'form-section' },
        h('label', null, 'Search for Item'),
        h('div', { class: 'input-group' },
          h('input', {
            type: 'text',
            class: 'form-input',
            placeholder: 'Search for food items...',
            value: searchQuery,
            style: 'flex: 1',
            oninput: (e) => setSearchQuery(e.target.value),
            onkeypress: (e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleSearch();
              }
            }
          }),
          h(Button, { 
            text: searching ? 'Searching...' : 'Search', 
            variant: 'primary',
            onClick: handleSearch,
            loading: searching
          })
        ),
        h('button', {
          type: 'button',
          class: 'btn-sm',
          onclick: () => {
            setShowSearch(false);
            setSearchResults([]);
            setSearchQuery('');
          },
          style: 'margin-top: 0.5rem;'
        }, '← Back to Manual Entry')
      ),
      
      // Search results
      searchResults.length > 0 ? h('div', { class: 'form-section' },
        h('label', null, 'Search Results'),
        h('div', { 
          class: 'list-container',
          style: 'max-height: 300px; overflow-y: auto;'
        },
          ...searchResults.map(product =>
            h('div', {
              class: 'list-item',
              style: 'cursor: pointer; transition: background 0.2s;',
              onclick: () => handleSelectItem(product),
              onmouseover: (e) => e.currentTarget.style.background = 'var(--color-bg-secondary)',
              onmouseout: (e) => e.currentTarget.style.background = 'var(--color-bg-light)'
            },
              h('div', { class: 'list-item-content' },
                h('div', { class: 'list-item-primary' }, product.product_name || 'Unknown Item'),
                h('div', { class: 'list-item-secondary' }, 
                  product.brands ? `Brand: ${product.brands}` : ''
                )
              ),
              h('span', { style: 'color: var(--color-primary); font-size: 0.9rem;' }, 'Select →')
            )
          )
        )
      ) : null
    ]
  );
}

function PantryList({ items }) {
  if (!items || items.length === 0) {
    return h(
      "ul",
      { class: "pantry-list" },
      h("li", null, "No items in pantry yet."),
    );
  }

  return h(
    "ul",
    { class: "pantry-list" },
    ...items.map((item) => {
      // Handle new format with Quantities array [{amount, unit}, ...]
      let quantityDisplay = "";
      if (item.Quantities && Array.isArray(item.Quantities)) {
        quantityDisplay = item.Quantities.map(
          (q) => `${q.amount} ${q.unit}`
        ).join(", ");
      } else if (item.Quantity !== undefined) {
        // Fallback to old format
        quantityDisplay = item.Quantity;
      }

      return h(
        "li",
        null,
        h("strong", null, item.ItemName),
        " — ",
        quantityDisplay
      );
    }),
  );
}

export function PantryContainer({ pantryItems = [] }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return h(
    "div",
    { id: "pantry-content" },
    h("h3", null, "Pantry Items"),
    h(
      "button",
      {
        class: "add-item-btn",
        onclick: () => setIsModalOpen(true),
      },
      "Add New Item",
    ),
    h(PantryList, { items: pantryItems }),
    h(AddItemModal, {
      isOpen: isModalOpen,
      onClose: () => setIsModalOpen(false),
    }),
  );
}

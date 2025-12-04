/**
 * recipes.js
 * Recipe management using hook.js components
 */

import { h, useState, render } from './hook.js';
import { Modal, FormInput, FormSelect, FormRow, DynamicList, CheckboxGroup,Alert,Button,useForm, useList} from './components.js';

const COURSE_OPTIONS = [
  { value: 'appetizer', text: 'Appetizer' },
  { value: 'main course', text: 'Main Course' },
  { value: 'side dish', text: 'Side Dish' },
  { value: 'dessert', text: 'Dessert' },
  { value: 'breakfast', text: 'Breakfast' },
  { value: 'snack', text: 'Snack' },
  { value: 'beverage', text: 'Beverage' }
];

const UNIT_OPTIONS = [
  { value: 'cup', text: 'cup' },
  { value: 'tbsp', text: 'tbsp' },
  { value: 'tsp', text: 'tsp' },
  { value: 'oz', text: 'oz' },
  { value: 'lb', text: 'lb' },
  { value: 'g', text: 'g' },
  { value: 'kg', text: 'kg' },
  { value: 'piece', text: 'piece' },
  { value: 'clove', text: 'clove' },
  { value: 'to taste', text: 'to taste' }
];

function AddRecipeModal(props) {
  const { isOpen, onClose, households, currentHouseholdId } = props;
  
  // sets form to start blank
  const [form, setField, resetForm] = useForm({
    recipeName: '',
    serves: '',
    preptime: '',
    cooktime: '',
    cuisine: '',
    course: 'main course'
  });
  
  const [ingName, setIngName] = useState('');
  const [ingAmount, setIngAmount] = useState('');
  const [ingUnit, setIngUnit] = useState('cup');
  
  const [instruction, setInstruction] = useState('');
  
  const [ingredients, addIngredient, removeIngredient, clearIngredients] = useList([]);
  const [instructions, addInstruction, removeInstruction, clearInstructions] = useList([]);
  
  const [selectedHouseholds, setSelectedHouseholds] = useState(
    currentHouseholdId ? [currentHouseholdId] : []
  );
  
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // ingredient addition
  const handleAddIngredient = () => {
    if (!ingName.trim()) {
      setError('Ingredient name is required');
      return;
    }
    if (!ingAmount || parseFloat(ingAmount) <= 0) {
      setError('Valid amount is required');
      return;
    }
    
    setError(null);
    addIngredient({ name: ingName.trim(), amount: ingAmount, unit: ingUnit });
    
    setIngName('');
    setIngAmount('');
    setIngUnit('cup');
  };

  // instruction addition
  const handleAddInstruction = () => {
    if (!instruction.trim()) {
      setError('Instruction text is required');
      return;
    }
    
    setError(null);
    addInstruction(instruction.trim());
    setInstruction('');
  };

  // form submission
  const handleSubmit = async () => {
    if (!form.recipeName.trim()) {
      setError('Recipe name is required');
      return;
    }
    if (selectedHouseholds.length === 0) {
      setError('Please select at least one household');
      return;
    }
    if (ingredients.length === 0) {
      setError('Please add at least one ingredient');
      return;
    }
    if (instructions.length === 0) {
      setError('Please add at least one instruction');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/recipes/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipeName: form.recipeName.trim(),
          serves: form.serves || '1',
          preptime: form.preptime || '0',
          cooktime: form.cooktime || '0',
          cuisine: form.cuisine || '',
          course: form.course || 'main course',
          householdIds: selectedHouseholds,
          ingredients: ingredients,
          instructions: instructions
        })
      });

      const result = await response.json();

      if (result.success) {
        handleClose();
        window.location.reload();
      } else {
        setError(result.error || 'Failed to add recipe');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    clearIngredients();
    clearInstructions();
    setSelectedHouseholds(currentHouseholdId ? [currentHouseholdId] : []);
    setError(null);
    setIngName('');
    setIngAmount('');
    setInstruction('');
    onClose();
  };

  const renderIngredient = (ing) => h('div', null,
    h('span', { class: 'list-item-primary' }, ing.name),
    h('span', { class: 'list-item-secondary' }, ` - ${ing.amount} ${ing.unit}`)
  );

  // Household options for checkboxes
  const householdOptions = households.map(h => ({
    value: h.id,
    text: h.name
  }));

  return h(Modal, {
    isOpen,
    onClose: handleClose,
    title: 'Add New Recipe',
    size: 'md',
    footer: [
      h(Button, { text: 'Cancel', variant: 'secondary', onClick: handleClose }),
      h(Button, { text: 'Add Recipe', variant: 'primary', onClick: handleSubmit, loading })
    ]
  },
    h(Alert, { type: 'error', message: error, onDismiss: () => setError(null) }),
    
    h(FormInput, {
      label: 'Recipe Name',
      name: 'recipeName',
      value: form.recipeName,
      onChange: setField,
      placeholder: 'Enter recipe name',
      required: true
    }),
    
    h(CheckboxGroup, {
      label: 'Add to Households',
      options: householdOptions,
      selected: selectedHouseholds,
      onChange: setSelectedHouseholds,
      showSelectAll: true
    }),
    
    h(FormRow, null,
      h(FormInput, {
        label: 'Servings',
        name: 'serves',
        type: 'number',
        value: form.serves,
        onChange: setField,
        placeholder: '4',
        min: 1
      }),
      h(FormInput, {
        label: 'Prep Time (min)',
        name: 'preptime',
        type: 'number',
        value: form.preptime,
        onChange: setField,
        placeholder: '15',
        min: 0
      }),
      h(FormInput, {
        label: 'Cook Time (min)',
        name: 'cooktime',
        type: 'number',
        value: form.cooktime,
        onChange: setField,
        placeholder: '30',
        min: 0
      })
    ),
    
    // Cuisine and course
    h(FormRow, null,
      h(FormInput, {
        label: 'Cuisine',
        name: 'cuisine',
        value: form.cuisine,
        onChange: setField,
        placeholder: 'e.g., Italian, Mexican'
      }),
      h(FormSelect, {
        label: 'Course',
        name: 'course',
        value: form.course,
        onChange: setField,
        options: COURSE_OPTIONS
      })
    ),
    
    // Ingredients list
    h(DynamicList, {
      label: 'Ingredients',
      items: ingredients,
      onRemove: removeIngredient,
      renderItem: renderIngredient,
      addButtonText: '+ Add',
      onAdd: handleAddIngredient,
      renderInputs: () => [
        h('input', {
          type: 'text',
          id: 'ing-name-input',
          class: 'form-input',
          placeholder: 'Name',
          value: ingName,
          style: 'flex: 2',
          oninput: (e) => setIngName(e.target.value)
        }),
        h('input', {
          type: 'number',
          id: 'ing-amount-input',
          class: 'form-input',
          placeholder: 'Amount',
          value: ingAmount,
          style: 'flex: 1',
          min: '0',
          step: '0.01',
          oninput: (e) => setIngAmount(e.target.value)
        }),
        h('select', {
          id: 'ing-unit-input',
          class: 'form-select',
          style: 'flex: 1',
          value: ingUnit,
          onchange: (e) => setIngUnit(e.target.value)
        },
          ...UNIT_OPTIONS.map(opt => 
            h('option', { value: opt.value }, opt.text)
          )
        )
      ]
    }),
    
    // Instructions list
    h(DynamicList, {
      label: 'Instructions',
      items: instructions,
      onRemove: removeInstruction,
      renderItem: (text) => h('span', null, text),
      addButtonText: 'Add Step',
      numbered: true,
      onAdd: handleAddInstruction,
      renderInputs: () => [
        h('textarea', {
          id: 'instruction-input',
          class: 'form-textarea',
          placeholder: 'Describe the step',
          rows: 2,
          value: instruction,
          style: 'flex: 1',
          oninput: (e) => setInstruction(e.target.value)
        })
      ]
    })
  );
}

/**
 * main recipes page 
 */
function RecipesPage(props) {
  const { userHouseholds = [], currentHouseholdId = null } = props;
  const [isModalOpen, setIsModalOpen] = useState(false);

  return h('div', { class: 'recipes-controls' },
    h('button', {
      class: 'add-recipe-btn',
      onclick: () => setIsModalOpen(true)
    }, '+ Add Recipe'),
    
    h(AddRecipeModal, {
      isOpen: isModalOpen,
      onClose: () => setIsModalOpen(false),
      households: userHouseholds,
      currentHouseholdId
    })
  );
}

export function initRecipes(config) {
  const container = document.getElementById('recipes-root');
  if (container) {
    render(h(RecipesPage, config), container);
  }
}

export function RecipesContainer(config) {
  const container = document.createElement('div');
  container.id = 'recipes-app-wrapper';
  
  setTimeout(() => {
    render(h(RecipesPage, config), container);
  }, 0);
  
  return container;
}
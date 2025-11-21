import { BuildModal } from './modal.js';

let currentHouseholds = [];
let currentHouseholdId = null;

function createRecipeModal() {
  const modal = new BuildModal({
    id: 'recipe-modal',
    title: 'Add New Recipe',
    size: 'md',
    
    fields: [
      {
        type: 'text',
        name: 'recipeName',
        label: 'Recipe Name',
        placeholder: 'Enter recipe name',
        required: true
      },
      {
        type: 'checkboxes',
        id: 'household-list',
        label: 'Add to Households',
        required: true,
        showSelectAll: true
      },
      {
        type: 'row',
        groups: [
          { label: 'Servings', name: 'serves', type: 'number', min: '1', placeholder: '4' },
          { label: 'Prep Time (min)', name: 'preptime', type: 'number', min: '0', placeholder: '15' },
          { label: 'Cook Time (min)', name: 'cooktime', type: 'number', min: '0', placeholder: '30' }
        ]
      },
      {
        type: 'row',
        groups: [
          { label: 'Cuisine', name: 'cuisine', placeholder: 'e.g., Italian, Mexican' },
          {
            label: 'Course',
            name: 'course',
            type: 'select',
            options: [
              { value: 'appetizer', text: 'Appetizer' },
              { value: 'main course', text: 'Main Course', selected: true },
              { value: 'side dish', text: 'Side Dish' },
              { value: 'dessert', text: 'Dessert' },
              { value: 'breakfast', text: 'Breakfast' },
              { value: 'snack', text: 'Snack' },
              { value: 'beverage', text: 'Beverage' }
            ]
          }
        ]
      },
      {
        type: 'list',
        id: 'ingredients-list',
        label: 'Ingredients',
        required: true,
        addButtonText: '+ Add',
        itemType: 'content',
        inputs: [
          { 
            id: 'new-ing-name', 
            type: 'text',
            placeholder: 'Name', 
            flex: 2,
            required: true  
          },
          { 
            id: 'new-ing-amount', 
            type: 'number',  
            placeholder: 'Amount', 
            flex: 1,
            required: true,
            min: '0',
            step: '0.01' // this allows decimals
          },
          { 
            id: 'new-ing-unit', 
            type: 'select', 
            flex: 1, 
            options: ['cup', 'tbsp', 'tsp', 'oz', 'lb', 'g', 'kg', 'piece', 'clove', 'to taste'] 
          }
        ]
      },
      {
        type: 'list',
        id: 'instructions-list',
        label: 'Instructions',
        required: true,
        addButtonText: 'Add Step',
        itemType: 'numbered',
        inputs: [
          { 
            id: 'new-instruction', 
            type: 'textarea', 
            placeholder: 'Describe the step',
            required: true
          }
        ]
      }
    ],
    
    buttons: [
      { text: 'Cancel', action: 'cancel' },
      { text: 'Add Recipe', action: 'submit', primary: true }
    ],
    
    onOpen: (modal) => {
      // Populate households after modal opens
      modal.populateCheckboxes('household-list', currentHouseholds, [currentHouseholdId]);
    },
    
    onSubmit: async (data, modal) => {
      // Validate
      if (!data.recipeName.trim()) {
        throw new Error('Recipe name is required');
      }
      
      if (!data['household-list'] || data['household-list'].length === 0) {
        throw new Error('Please select at least one household');
      }
      
      if (!data['ingredients-list'] || data['ingredients-list'].length === 0) {
        throw new Error('Please add at least one ingredient');
      }
      
      if (!data['instructions-list'] || data['instructions-list'].length === 0) {
        throw new Error('Please add at least one instruction');
      }
      
      // Submit to server
      const response = await fetch('/recipes/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipeName: data.recipeName.trim(),
          serves: data.serves || "1",
          preptime: data.preptime || "0",
          cooktime: data.cooktime || "0",
          cuisine: data.cuisine || "",
          course: data.course || "main course",
          householdIds: data['household-list'],
          ingredients: data['ingredients-list'].map(ing => ({
            name: ing['ing-name'],
            amount: ing['ing-amount'],
            unit: ing['ing-unit']
          })),
          instructions: data['instructions-list'].map(inst => inst.instruction)
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        modal.close();
        window.location.reload();
      } else {
        throw new Error(result.error || 'Failed to add recipe');
      }
    }
  });
  
  modal.show();
}

export function RecipesContainer({ userHouseholds, currentHouseholdId: hid }) {
  currentHouseholds = userHouseholds;
  currentHouseholdId = hid;

  const button = document.createElement('button');
  button.className = 'add-recipe-btn';
  button.textContent = '+ Add Recipe';
  button.onclick = createRecipeModal;

  const container = document.createElement('div');
  container.appendChild(button);

  return container;
}
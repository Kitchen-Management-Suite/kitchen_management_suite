import { h, useState, render } from "./hook.js";

function AddRecipeModal({ isOpen, onClose }) {
  const [recipeName, setRecipeName] = useState("");
  const [serves, setServes] = useState("");
  const [preptime, setPreptime] = useState("");
  const [cooktime, setCooktime] = useState("");
  const [ingredients, setIngredients] = useState([{ name: "", amount: "" }]);
  const [instructions, setInstructions] = useState([""]);

  if (!isOpen) {
    return h("div", { class: "modal" });
  }

  const addIngredient = () => {
    setIngredients([...ingredients, { name: "", amount: "" }]);
  };

  const removeIngredient = (index) => {
    if (ingredients.length > 1) {
      setIngredients(ingredients.filter((_, i) => i !== index));
    }
  };

  const updateIngredient = (index, field, value) => {
    const updated = [...ingredients];
    updated[index] = { ...updated[index], [field]: value };
    setIngredients(updated);
  };

  const addInstruction = () => {
    setInstructions([...instructions, ""]);
  };

  const removeInstruction = (index) => {
    if (instructions.length > 1) {
      setInstructions(instructions.filter((_, i) => i !== index));
    }
  };

  const updateInstruction = (index, value) => {
    const updated = [...instructions];
    updated[index] = value;
    setInstructions(updated);
  };

  return h(
    "div",
    {
      class: "modal active",
      onclick: (e) => {
        if (e.target.classList.contains("modal")) {
          onClose();
        }
      },
    },
    h(
      "div",
      { class: "modal-content recipe-modal" },
      h(
        "form",
        { class: "recipe-form", onsubmit: (e) => e.preventDefault() },
        h(
          "div",
          { class: "form-section" },
          h("label", null, "Recipe Name"),
          h("input", {
            type: "text",
            value: recipeName,
            oninput: (e) => setRecipeName(e.target.value),
            placeholder: "Enter recipe name",
          }),
        ),

        h(
          "div",
          { class: "form-row" },
          h(
            "div",
            { class: "form-group" },
            h("label", null, "Servings"),
            h("input", {
              type: "number",
              min: "1",
              value: serves,
              oninput: (e) => setServes(e.target.value),
              placeholder: "e.g. 4",
            }),
          ),
          h(
            "div",
            { class: "form-group" },
            h("label", null, "Prep Time (min)"),
            h("input", {
              type: "number",
              min: "0",
              value: preptime,
              oninput: (e) => setPreptime(e.target.value),
              placeholder: "e.g. 15",
            }),
          ),
          h(
            "div",
            { class: "form-group" },
            h("label", null, "Cook Time (min)"),
            h("input", {
              type: "number",
              min: "0",
              value: cooktime,
              oninput: (e) => setCooktime(e.target.value),
              placeholder: "e.g. 30",
            }),
          ),
        ),

        h(
          "div",
          { class: "form-section" },
          h(
            "div",
            { class: "section-header" },
            h("label", null, "Ingredients"),
            h(
              "button",
              {
                type: "button",
                class: "add-item-btn",
                onclick: addIngredient,
              },
              "+ Add Ingredient",
            ),
          ),
          ...ingredients.map((ing, index) =>
            h(
              "div",
              { class: "ingredient-row", key: index },
              h("input", {
                type: "text",
                placeholder: "Ingredient name",
                value: ing.name,
                oninput: (e) => updateIngredient(index, "name", e.target.value),
              }),
              h("input", {
                type: "text",
                placeholder: "Amount",
                value: ing.amount,
                oninput: (e) =>
                  updateIngredient(index, "amount", e.target.value),
              }),
              ...(ingredients.length > 1
                ? [
                    h(
                      "button",
                      {
                        type: "button",
                        class: "remove-btn",
                        onclick: () => removeIngredient(index),
                      },
                      "×",
                    ),
                  ]
                : []),
            ),
          ),
        ),

        h(
          "div",
          { class: "form-section" },
          h(
            "div",
            { class: "section-header" },
            h("label", null, "Instructions"),
            h(
              "button",
              {
                type: "button",
                class: "add-item-btn",
                onclick: addInstruction,
              },
              "+ Add Step",
            ),
          ),
          ...instructions.map((inst, index) =>
            h(
              "div",
              { class: "instruction-row", key: index },
              h("span", { class: "step-number" }, `${index + 1}.`),
              h("textarea", {
                placeholder: "Enter instruction step",
                value: inst,
                oninput: (e) => updateInstruction(index, e.target.value),
                rows: "2",
              }),
              ...(instructions.length > 1
                ? [
                    h(
                      "button",
                      {
                        type: "button",
                        class: "remove-btn",
                        onclick: () => removeInstruction(index),
                      },
                      "×",
                    ),
                  ]
                : []),
            ),
          ),
        ),

        h(
          "div",
          { class: "form-actions" },
          h(
            "button",
            {
              type: "button",
              class: "cancel-btn",
              onclick: onClose,
            },
            "Cancel",
          ),
          h(
            "button",
            {
              type: "submit",
              class: "submit-btn",
            },
            "Add Recipe",
          ),
        ),
      ),
    ),
  );
}

export function RecipesContainer() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return h(
    "div",
    null,
    h(
      "button",
      {
        class: "add-recipe-btn",
        onclick: () => setIsModalOpen(true),
      },
      "+ Add Recipe",
    ),
    h(AddRecipeModal, {
      isOpen: isModalOpen,
      onClose: () => setIsModalOpen(false),
    }),
  );
}

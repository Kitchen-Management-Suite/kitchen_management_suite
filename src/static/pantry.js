import { h, useState, render } from "./hook.js";

function AddItemModal({ isOpen, onClose }) {
  return h(
    "div",
    {
      class: isOpen ? "modal active" : "modal",
      onclick: (e) => {
        if (e.target.classList.contains("modal")) {
          onClose();
        }
      },
    },
    h(
      "div",
      { class: "modal-content modal-md" },
      h("h3", null, "Add Item to Pantry"),
      h(
        "div",
        { class: "modal-buttons" },
        h(
          "button",
          {
            class: "modal-btn manual",
            onclick: onClose,
          },
          "Manual Add",
        ),
        h(
          "button",
          {
            class: "modal-btn scan",
            disabled: true,
          },
          "Scan",
        ),
      ),
    ),
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

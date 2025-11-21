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
    ...items.map((item) =>
      h("li", null, h("strong", null, item.ItemName), " — ", item.Quantity),
    ),
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

/* hook.js
 * react-free react :sob:
 */

let currentComponent = null;
let hookIndex = 0;
const roots = new Map(); // track mounted components for re-renders

/* creates virtual dom element with type, props, and children
 */
export function h(type, props, ...children) {
  return { type, props: props || {}, children: children.flat() };
}

/* converts virtual node to real dom element
 * handles text nodes, function components, and regular elements
 * processes children and sets attributes/events
 */
function createDom(vnode) {
  if (vnode == null || vnode === false) return document.createTextNode("");
  if (typeof vnode === "string" || typeof vnode === "number")
    return document.createTextNode(vnode);

  if (typeof vnode.type === "function") {
    const component = { vnode, hooks: [], dom: null };
    currentComponent = component;
    hookIndex = 0;
    const rendered = vnode.type(vnode.props || {});
    const dom = createDom(rendered);
    component.dom = dom;
    currentComponent = null;
    return dom;
  }

  const dom = document.createElement(vnode.type);
  for (const [k, v] of Object.entries(vnode.props || {})) {
    if (k.startsWith("on") && typeof v === "function")
      dom.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v != null) dom.setAttribute(k, v);
  }

  vnode.children.map(createDom).forEach((child) => dom.appendChild(child));
  return dom;
}

/* checks if two virtual nodes are different
 * compares types, content, and element types
 * returns true if nodes need complete replacement
 */
function isChanged(a, b) {
  return (
    typeof a !== typeof b ||
    (typeof a === "string" && a !== b) ||
    a.type !== b.type
  );
}

/* updates dom element attributes and event listeners
 * removes old attributes, adds new ones, handles event binding
 * preserves existing dom structure while updating properties
 */
function updateDom(dom, prevProps, nextProps) {
  for (const [k, v] of Object.entries(prevProps))
    if (!(k in nextProps)) dom.removeAttribute(k);
  for (const [k, v] of Object.entries(nextProps)) {
    if (k.startsWith("on") && typeof v === "function") {
      dom[k.toLowerCase()] = v;
    } else if (v != null) dom.setAttribute(k, v);
  }
}

/* updates dom by comparing virtual nodes
 * reuses existing dom elements when possible, creates new ones when needed
 * recursively patches all children and handles component re-rendering
 */
function patch(dom, oldVNode, newVNode) {
  if (!oldVNode) return createDom(newVNode);
  if (!newVNode) return document.createTextNode("");
  if (isChanged(oldVNode, newVNode)) return createDom(newVNode);

  if (typeof newVNode.type === "function") {
    const rendered = newVNode.type(newVNode.props || {});
    return patch(dom, oldVNode.rendered, rendered);
  }

  updateDom(dom, oldVNode.props || {}, newVNode.props || {});

  const childCount = Math.max(
    oldVNode.children.length,
    newVNode.children.length,
  );
  for (let i = 0; i < childCount; i++) {
    const child = dom.childNodes[i];
    const newChild = patch(child, oldVNode.children[i], newVNode.children[i]);
    if (newChild !== child) dom.replaceChild(newChild, child);
  }
  return dom;
}

/* mounts virtual node to dom container
 * handles initial mount and subsequent updates via patching
 * tracks mounted roots for efficient re-renders
 */
export function render(vnode, container) {
  const existing = roots.get(container);
  if (!existing) {
    const dom = createDom(vnode);
    container.innerHTML = "";
    container.appendChild(dom);
    roots.set(container, { vnode, dom });
  } else {
    const { vnode: oldVNode, dom } = existing;
    const newDom = patch(dom, oldVNode, vnode);
    roots.set(container, { vnode, dom: newDom });
  }
}

/* provides state management for components
 * returns current state value and setter function
 * triggers re-render when state changes
 */
export function useState(initial) {
  const comp = currentComponent;
  const i = hookIndex++;
  if (comp.hooks[i] === undefined) comp.hooks[i] = initial;
  const setState = (val) => {
    comp.hooks[i] = typeof val === "function" ? val(comp.hooks[i]) : val;
    rerenderRoot(comp.vnode);
  };
  return [comp.hooks[i], setState];
}

/* handles side effects with dependency tracking
 * manages cleanup functions for effects
 */
export function useEffect(fn, deps) {
  const comp = currentComponent;
  const i = hookIndex++;
  const prev = comp.hooks[i];
  let changed = true;
  if (prev && deps) changed = deps.some((d, j) => d !== prev.deps[j]);
  if (changed) {
    comp.hooks[i] = { deps, cleanup: fn() };
  }
}

/* triggers re-render for component root
 * finds matching mounted component and updates its container
 * enables reactive updates when state changes
 */
function rerenderRoot(vnode) {
  for (const [container, root] of roots.entries()) {
    if (root.vnode.type === vnode.type) {
      render(vnode, container);
      break;
    }
  }
}

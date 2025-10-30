/* hook.js
 * react-free react :sob:
 */

let currentComponent = null;
let hookIndex = 0;
const roots = new Map(); // track mounted components for re-renders

export function h(type, props, ...children) {
  return { type, props: props || {}, children: children.flat() };
}

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

function isChanged(a, b) {
  return (
    typeof a !== typeof b ||
    (typeof a === "string" && a !== b) ||
    a.type !== b.type
  );
}

function updateDom(dom, prevProps, nextProps) {
  for (const [k, v] of Object.entries(prevProps))
    if (!(k in nextProps)) dom.removeAttribute(k);
  for (const [k, v] of Object.entries(nextProps)) {
    if (k.startsWith("on") && typeof v === "function") {
      dom[k.toLowerCase()] = v;
    } else if (v != null) dom.setAttribute(k, v);
  }
}

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

function rerenderRoot(vnode) {
  for (const [container, root] of roots.entries()) {
    if (root.vnode.type === vnode.type) {
      render(vnode, container);
      break;
    }
  }
}

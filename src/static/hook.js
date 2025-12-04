/* hook.js
 * react-free react :sob:
 */

let currentComponent = null;
let hookIndex = 0;
let currentRoot = null;
const roots = new Map(); // track mounted components for re-renders

/** 
 * creates virtual dom element with type, props, and children
 */
export function h(type, props, ...children) {
  const flatChildren = children.flat().filter(c => c != null && c !== false);
  const finalProps = props || {};
  if (typeof type === 'function' && flatChildren.length > 0) {
    finalProps.children = flatChildren;
  }
  return { type, props: finalProps, children: flatChildren };
}

/**  
 * converts virtual node to real dom element
 * handles text nodes, function components, and regular elements
 * processes children and sets attributes/events
 */
function createDom(vnode) {
  if (vnode == null || vnode === false) return document.createTextNode("");
  if (typeof vnode === "string" || typeof vnode === "number")
    return document.createTextNode(vnode);

  if (typeof vnode.type === 'function') {
    const component = { 
      vnode, 
      hooks: [], 
      dom: null, 
      rendered: null,
      rootContainer: currentRoot
    };
    
    currentComponent = component;
    hookIndex = 0;
    
    const rendered = vnode.type(vnode.props || {});
    component.rendered = rendered;
    
    const dom = createDom(rendered);
    component.dom = dom;
    dom.__component = component;
    
    currentComponent = null;
    return dom;
  }

  const dom = document.createElement(vnode.type);
  applyProps(dom, vnode.props || {});
  
  for (const child of vnode.children) {
    dom.appendChild(createDom(child));
  }
  
  return dom;
}

/**
 * apply props to DOM element
 * handles controlled inputs properly
 */
function applyProps(dom, props, oldProps = {}) {
  // Remove old props
  for (const key of Object.keys(oldProps)) {
    if (!(key in props) && key !== 'children') {
      if (key.startsWith('on')) {
        dom[key.toLowerCase()] = null;
      } else if (key !== 'ref') {
        dom.removeAttribute(key === 'className' ? 'class' : key);
      }
    }
  }
  
  // set new props
  for (const [key, value] of Object.entries(props)) {
    if (key === 'children') continue;
    
    if (key === 'ref' && typeof value === 'object') {
      value.current = dom;
    } else if (key.startsWith('on') && typeof value === 'function') {
      dom[key.toLowerCase()] = value;
    } else if (key === 'style') {
      if (typeof value === 'object') {
        Object.assign(dom.style, value);
      } else if (typeof value === 'string') {
        dom.style.cssText = value;
      }
    } else if (key === 'class' || key === 'className') {
      dom.className = value || '';
    } else if (key === 'value' && (dom.tagName === 'INPUT' || dom.tagName === 'TEXTAREA' || dom.tagName === 'SELECT')) {
      // set as property, only if changed
      if (dom.value !== String(value ?? '')) {
        dom.value = value ?? '';
      }
    } else if (key === 'checked' && dom.tagName === 'INPUT') {
      dom.checked = !!value;
    } else if (value != null && value !== false) {
      dom.setAttribute(key, value === true ? '' : value);
    } else {
      dom.removeAttribute(key);
    }
  }
}

/* checks if two virtual nodes are different
 * compares types, content, and element types
 * returns true if nodes need complete replacement
 */
function isChanged(oldNode, newNode) {
  return (
    typeof oldNode !== typeof newNode ||
    (typeof oldNode === 'string' && oldNode !== newNode) ||
    (typeof oldNode === 'number' && oldNode !== newNode) ||
    oldNode?.type !== newNode?.type
  );
}

/* updates dom by comparing virtual nodes
 * reuses existing dom elements when possible, creates new ones when needed
 * recursively patches all children and handles component re-rendering
 */
function patch(dom, oldVNode, newVNode) {
  if (!oldVNode) return createDom(newVNode);
  if (!newVNode) return document.createTextNode('');
  if (isChanged(oldVNode, newVNode)) return createDom(newVNode);

  if (typeof newVNode.type === 'function') {
    const existingComponent = dom?.__component;
    
    let component;
    if (existingComponent && existingComponent.vnode.type === newVNode.type) {
      component = existingComponent;
    } else {
      component = { vnode: newVNode, hooks: [], dom: null, rendered: null, rootContainer: currentRoot };
    }
    
    if (!component.rootContainer) component.rootContainer = currentRoot;
    
    const oldRendered = component.rendered;
    component.vnode = newVNode;
    
    const prevComponent = currentComponent;
    const prevHookIndex = hookIndex;
    currentComponent = component;
    hookIndex = 0;
    
    const rendered = newVNode.type(newVNode.props || {});
    component.rendered = rendered;
    
    const newDom = patch(dom, oldRendered, rendered);
    component.dom = newDom;
    newDom.__component = component;
    
    currentComponent = prevComponent;
    hookIndex = prevHookIndex;
    
    return newDom;
  }

  // update props
  applyProps(dom, newVNode.props || {}, oldVNode.props || {});

  const oldChildren = oldVNode.children || [];
  const newChildren = newVNode.children || [];
  const maxLen = Math.max(oldChildren.length, newChildren.length);
  
  for (let i = maxLen - 1; i >= 0; i--) {
    const oldChild = oldChildren[i];
    const newChild = newChildren[i];
    const existingDom = dom.childNodes[i];
    
    if (!newChild && existingDom) {
      dom.removeChild(existingDom);
    } else if (newChild && !existingDom) {
      const newDom = patch(null, null, newChild);
      if (i < dom.childNodes.length) {
        dom.insertBefore(newDom, dom.childNodes[i]);
      } else {
        dom.appendChild(newDom);
      }
    } else if (newChild && existingDom) {
      const newDom = patch(existingDom, oldChild, newChild);
      if (newDom !== existingDom) {
        dom.replaceChild(newDom, existingDom);
      }
    }
  }
  
  return dom;
}

/* mounts virtual node to dom container
 * handles initial mount and subsequent updates via patching
 * tracks mounted roots for efficient re-renders
 */
export function render(vnode, container) {
  const existing = roots.get(container);
  
  // save focus state -> for modal forms
  const active = document.activeElement;
  const focusInfo = active ? {
    id: active.id,
    name: active.name,
    tag: active.tagName,
    start: active.selectionStart,
    end: active.selectionEnd
  } : null;
  
  // save scroll positions -> for modal forms
  const scrolls = new Map();
  container.querySelectorAll('.modal-body, .modal-content').forEach(el => {
    if (el.scrollTop > 0) scrolls.set(el.className, el.scrollTop);
  });
  
  const prevRoot = currentRoot;
  currentRoot = container;
  
  try {
    if (!existing) {
      const dom = createDom(vnode);
      container.innerHTML = '';
      container.appendChild(dom);
      roots.set(container, { vnode, dom });
    } else {
      const newDom = patch(existing.dom, existing.vnode, vnode);
      roots.set(container, { vnode, dom: newDom });
    }
  } finally {
    currentRoot = prevRoot;
  }
  
  container.querySelectorAll('.modal-body, .modal-content').forEach(el => {
    const saved = scrolls.get(el.className);
    if (saved) el.scrollTop = saved;
  });
  
  if (focusInfo && (focusInfo.id || focusInfo.name)) {
    const el = focusInfo.id ? document.getElementById(focusInfo.id) 
             : document.querySelector(`[name="${focusInfo.name}"]`);
    if (el && (focusInfo.tag === 'INPUT' || focusInfo.tag === 'TEXTAREA' || focusInfo.tag === 'SELECT')) {
      el.focus({ preventScroll: true });
      // Restore cursor for text inputs only
      if (focusInfo.start != null && (el.type === 'text' || el.type === 'search' || el.type === 'tel' || el.type === 'url' || focusInfo.tag === 'TEXTAREA')) {
        try { el.setSelectionRange(focusInfo.start, focusInfo.end); } catch(e) {}
      }
    }
  }
}

/* provides state management for components
 * returns current state value and setter function
 * triggers re-render when state changes
 */
export function useState(initial) {
  const comp = currentComponent;
  const idx = hookIndex++;
  
  if (comp.hooks[idx] === undefined) {
    comp.hooks[idx] = typeof initial === 'function' ? initial() : initial;
  }
  
  const setState = (value) => {
    const newValue = typeof value === 'function' ? value(comp.hooks[idx]) : value;
    if (!Object.is(newValue, comp.hooks[idx])) {
      comp.hooks[idx] = newValue;
      rerenderComponent(comp);
    }
  };
  
  return [comp.hooks[idx], setState];
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

/**
 * reference hook
 */
export function useRef(initial) {
  const comp = currentComponent;
  const i = hookIndex++;
  if (comp.hooks[i] === undefined) {
    comp.hooks[i] = { current: initial };
  }
  return comp.hooks[i];
}

/**
 * memoization hook
 */
export function useMemo(fn, deps) {
  const comp = currentComponent;
  const i = hookIndex++;
  const prev = comp.hooks[i];
  
  const changed = !prev || !prev.deps ||
    deps.length !== prev.deps.length ||
    deps.some((d, id) => !Object.is(d, prev.deps[id]));
  
  if (changed) {
    const value = fn();
    comp.hooks[i] = { deps, value };
    return value;
  }
  return prev.value;
}

/**
 * callback hook
 */
export function useCallback(fn, deps) {
  return useMemo(() => fn, deps);
}

/* triggers re-render for component
 * finds matching mounted component and updates its container
 * enables reactive updates when state changes
 */
function rerenderComponent(comp) {
  const container = comp.rootContainer;
  if (!container) return;
  const root = roots.get(container);
  if (root) render(root.vnode, container);
}

export function Fragment(props) {
  return props.children;
}
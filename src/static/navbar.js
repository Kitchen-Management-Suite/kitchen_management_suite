/* navbar.js
 * Modular navbar component matching existing HTML structure
 * Created By: Rohan plante
 * Date Created: 11/01/2025
 */

import { h } from './hook.js';

/**
 * Navbar component that adapts to user logged in state
 * @param {Object} props - Component properties
 * @param {boolean} props.isLoggedIn - Whether user is logged in
 * @param {Array} props.households - List of user's households
 * @param {number} props.currentHouseholdId - Currently selected household ID
 * @param {boolean} props.showHouseholdSelector - Whether to show household selector
 * @param {string} props.currentEndpoint - Current Flask endpoint/route name
 */
export function Navbar(props) {
  const { 
    isLoggedIn = false, 
    households = [],
    currentHouseholdId = null,
    showHouseholdSelector = false,
    currentEndpoint = 'index'
  } = props;

  // Helper to check if link should be active
  const isActive = (endpoint) => {
    // Handle recipes blueprint routes
    if (endpoint === 'recipes') {
      return currentEndpoint === 'recipes' || currentEndpoint.startsWith('recipes.');
    }
    return currentEndpoint === endpoint;
  };

  // Handle household switch
  const switchHousehold = (e) => {
    const householdId = e.target.value;
    // Redirect to switch_household route
    window.location.href = `/switch_household/${householdId}`;
  };

  if (isLoggedIn) {
    // Logged in navbar
    return h('header', null,
      h('nav', null,
        h('div', { class: 'nav-with-dropdown' },
          h('div', { class: 'nav-links' },
            h('a', { 
              href: '/', 
              class: isActive('index') ? 'active' : '' 
            }, 'Home'),
            h('a', { 
              href: '/recipes', 
              class: isActive('recipes') ? 'active' : '' 
            }, 'Recipes'),
            h('a', { 
              href: '/account', 
              class: isActive('account') ? 'active' : '' 
            }, 'Account'),
            h('a', { 
              href: '/pantry', 
              class: isActive('pantry') ? 'active' : '' 
            }, 'Pantry'),
            h('a', { href: '/logout' }, 'Logout')
          ),
          
          // Household Selector / Create/Join Button
          showHouseholdSelector ? (
            households.length > 0 ?
            // If user in housholds, render dropdown + button
            h('div', { class: 'household-selector' },
              h('label', { for: 'household-select' }, 'Household: '),
              h('select', {
                id: 'household-select',
                onchange: switchHousehold
              },
                ...households.map(household =>
                  h('option', {
                    value: household.id,
                    selected: household.id === currentHouseholdId ? true : undefined
                  }, household.name)
                )
              ),
              h('a', {
                href: '/household/manage',
                class: 'household-add-btn',
                title: 'Create or Join Household'
              }, '+')
            )
          :
            // If user not in a household, only render create/join button
            h('div', { class: 'household-selector' },
              h('a', {
                href: '/household/manage',
                class: 'household-create-btn'
              }, 'Create or Join Household')
            )
          ) : null
        )
      )
    );
  } else {
    // Logged out navbar
    return h('header', null,
      h('nav', null,
        h('div', { class: 'nav-links' },
          h('a', { 
            href: '/', 
            class: isActive('index') ? 'active' : '' 
          }, 'Home'),
          h('a', { 
            href: '/login', 
            class: isActive('auth.login') ? 'active' : '' 
          }, 'Login'),
          h('a', { 
            href: '/register', 
            class: isActive('auth.register') ? 'active' : '' 
          }, 'Register')
        )
      )
    );
  }
}

/**
 * Navbar container that uses server-provided data
 * This is the main export for easy integration
 */
export function NavbarContainer() {
  // Get navbar data passed from Flask via window object
  const navbarData = window.navbarData || {
    isLoggedIn: false,
    households: [],
    currentHouseholdId: null,
    showHouseholdSelector: false,
    currentEndpoint: 'index'
  };

  return h(Navbar, navbarData);
}
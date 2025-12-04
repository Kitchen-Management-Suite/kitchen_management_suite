/* navbar.js
 * Vertical sidebar navigation component
 * Created By: Rohan Plante
 * Date Created: 11/01/2025
 */

import { h } from './hook.js';

export function Navbar(props) {
  const {
    isLoggedIn = false,
    households = [],
    currentHouseholdId = null,
    showHouseholdSelector = true,
    currentEndpoint = 'index',
    userName = 'User',
    username = 'username',
    userRole = null,
    isAdmin = false
  } = props;

  const isActive = (endpoint) => {
    console.log(currentEndpoint, endpoint);
    return currentEndpoint.includes(endpoint);
  };

  const switchHousehold = (e) => {
    const householdId = e.target.value;
    const currentPath = window.location.pathname;
    window.location.href = `/switch_household/${householdId}?next=${encodeURIComponent(currentPath)}`;
  };

  const toggleDropdown = (e) => {
    e.stopPropagation();
    const dropdown = e.currentTarget.parentElement.querySelector('.profile-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('active');
    }
  };

  const setupDropdownClose = (element) => {
    if (!element) return;
    
    const closeDropdown = (e) => {
      const dropdown = element.querySelector('.profile-dropdown');
      const icon = element.querySelector('.profile-icon');
      if (dropdown && !icon.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('active');
      }
    };
    
    setTimeout(() => {
      document.addEventListener('click', closeDropdown);
    }, 0);
  };

  const toggleMobileMenu = (e) => {
    e.stopPropagation();
    const sidebar = document.querySelector('.sidebar-nav');
    if (sidebar) {
      sidebar.classList.toggle('mobile-open');
    }
  };

  if (isLoggedIn) {
    const initials = userName.split(' ').map(n => n[0]).join('').toUpperCase();

    return h('div', null,
      h('button', { 
        class: 'mobile-burger',
        onclick: toggleMobileMenu,
        'aria-label': 'Toggle menu'
      }, '☰'),

      h('nav', { 
        class: 'sidebar-nav',
        ref: setupDropdownClose
      },
        h('div', { class: 'profile-section' },
          h('div', { class: 'profile-header' },
            h('div', { 
              class: 'profile-icon',
              onclick: toggleDropdown
            }, initials),
            h('div', { class: 'profile-info' },
              h('div', { class: 'profile-name' }, userName),
              h('div', { class: 'profile-username' }, '@' + username)
            ),
            h('div', { 
              class: 'profile-dropdown',
              onclick: (e) => e.stopPropagation()
            },
              h('a', { href: '/settings' }, 'Account Settings'),
              h('a', { href: '/manage_user_profile'}, 'User Profile'),
              h('a', { href: '/logout', class: 'logout-btn'}, 'Logout')
            )
          )
        ),

        showHouseholdSelector ? (
          h('div', { class: 'household-selector' },
            households.length > 0 ? 
              h('div', null,
                h('div', { class: 'household-selector-row' },
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
              )
            :
              h('a', {
                href: '/household/manage',
                class: 'household-create-btn'
              }, 'Create or Join Household')
          )
        ) : null,

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
            href: '/pantry',
            class: isActive('pantry') ? 'active' : ''
          }, 'Pantry'),
          h('a', {
            href: '/calorieTracking',
            class: isActive('calorieTracking') ? 'active' : ''
          }, 'Track Calories'),
          isAdmin ? h('a', {
            href: '/household/settings',
            class: isActive('household.settings') ? 'active' : ''
          }, 'Household Settings') : null
        ),

        h('div', { class: 'sidebar-footer' },
          h('p', null, '© 2025 Kitchen Management Suite')
        )
      )
    );
  } else {
    return h('nav', { class: 'public-nav' },
      h('div', null, h('strong', null, 'Kitchen Management Suite')),
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
    );
  }
}

export function NavbarContainer() {
  const navbarData = window.navbarData || {
    isLoggedIn: false,
    households: [],
    currentHouseholdId: null,
    showHouseholdSelector: false,
    currentEndpoint: 'index',
    userName: null,
    username: null,
    userRole: null,
    isAdmin: false
  };

  return h(Navbar, navbarData);
}
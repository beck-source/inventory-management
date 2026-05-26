import { ref, computed, defineComponent, h } from 'vue'

export function createRouter(routes) {
  const currentPath = ref(window.location.pathname)

  const routeMap = Object.fromEntries(routes.map(r => [r.path, r.component]))

  const matchedComponent = computed(() => routeMap[currentPath.value] ?? routeMap['/'])

  const RouterLink = defineComponent({
    name: 'RouterLink',
    inheritAttrs: false,
    props: {
      to: { type: String, required: true }
    },
    setup(props, { slots, attrs }) {
      const navigate = (e) => {
        e.preventDefault()
        window.history.pushState(null, '', props.to)
        currentPath.value = props.to
      }
      return () => h('a', { href: props.to, onClick: navigate, ...attrs }, slots.default?.())
    }
  })

  const RouterView = defineComponent({
    name: 'RouterView',
    setup() {
      return () => h(matchedComponent.value)
    }
  })

  return {
    install(app) {
      window.addEventListener('popstate', () => {
        currentPath.value = window.location.pathname
      })

      app.config.globalProperties.$route = {
        get path() {
          return currentPath.value
        }
      }

      app.component('RouterLink', RouterLink)
      app.component('router-link', RouterLink)
      app.component('RouterView', RouterView)
      app.component('router-view', RouterView)
    }
  }
}

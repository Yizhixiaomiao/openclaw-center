import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../components/layout/AppLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/DashboardView.vue'),
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/users/UserList.vue'),
        meta: { roles: ['admin', 'support'] },
      },
      {
        path: 'users/:id',
        name: 'UserDetail',
        component: () => import('../views/users/UserDetail.vue'),
        meta: { roles: ['admin', 'support'] },
      },
      {
        path: 'machines',
        name: 'Machines',
        component: () => import('../views/machines/MachineList.vue'),
      },
      {
        path: 'machines/:id',
        name: 'MachineDetail',
        component: () => import('../views/machines/MachineDetail.vue'),
      },
      {
        path: 'scenarios',
        name: 'Scenarios',
        component: () => import('../views/scenarios/ScenarioList.vue'),
        meta: { roles: ['admin', 'support'] },
      },
      {
        path: 'prompts',
        name: 'Prompts',
        component: () => import('../views/prompts/TemplateList.vue'),
        meta: { roles: ['admin', 'support'] },
      },
      {
        path: 'prompts/:id',
        name: 'TemplateDetail',
        component: () => import('../views/prompts/TemplateDetail.vue'),
        meta: { roles: ['admin', 'support'] },
      },
      {
        path: 'skills',
        name: 'Skills',
        component: () => import('../views/skills/SkillList.vue'),
      },
      {
        path: 'deploy',
        name: 'Deploy',
        component: () => import('../views/deploy/DeployTaskList.vue'),
        meta: { roles: ['admin', 'support', 'ops'] },
      },
      {
        path: 'plans',
        name: 'Plans',
        component: () => import('../views/plans/PlanList.vue'),
        meta: { roles: ['admin'] },
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('../views/monitor/MonitorView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.public) return next()
  if (!getToken()) return next('/login')
  next()
})

export default router

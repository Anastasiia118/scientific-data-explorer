import { createRouter, createWebHistory } from 'vue-router'
import DatasetListView from '../views/DatasetListView.vue'
import DatasetDetailView from '../views/DatasetDetailView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dataset-list', component: DatasetListView },
    {
      // Only numeric ids match; the param is passed to the view as a number.
      path: '/datasets/:id(\\d+)',
      name: 'dataset-detail',
      component: DatasetDetailView,
      props: (route) => ({ id: Number(route.params.id) }),
    },
  ],
})

export default router

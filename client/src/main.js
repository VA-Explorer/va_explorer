import Vue from 'vue'
import App from './App.vue'
import store from '@/store/index'
import '@/styles/styles.css'
import 'vuesalize/dist/vuesalize.css'
import StackedBarChart from "vuesalize"
import LineChart from "vuesalize"
import BaseLegend from "vuesalize"

Vue.config.productionTip = false

Vue.use(StackedBarChart, LineChart, BaseLegend)

new Vue({
    render: h => h(App),
    store,
}).$mount('#app')

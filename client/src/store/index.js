import Vue from 'vue'
import Vuex from 'vuex'
import axios from "axios";

import {rollup, rollups} from "d3-array";
import {timeMonth} from "d3-time";

Vue.use(Vuex)

export default new Vuex.Store({
    state: {
        rawdata: [],
        invalid: '',
        borders: "district"
    },
    getters: {
        listOfCauses(state) {
            return [...new Set(state.rawdata.map(item => item.cause))].sort()
        },
        listOfDistrictAndProvinces(state) {
            const provinces = [...new Set(state.rawdata.map(item => item.province))]
            const districts = [...new Set(state.rawdata.map(item => item.district))]
            return [...provinces, ...districts].sort()
        },
        filteredData(state) {
            return state.rawdata
                .filter(item => item.active)
                .map(item => ({
                    ...item,
                    province: item.province.split(' ')[0],
                    district: item.district.split(' ')[0]
                }))
        },
        highlightsSummaries(state, getters) {
            return {
                "Coded VAs": getters.filteredData.length,
                "Uncoded VAs": state.invalid.length,
                "Active Facilities": [...new Set(getters.filteredData.map(item => item.location))].length,
            }
        },
        geographicSums(state, getters) {
            let geo_groups = rollups(getters.filteredData, v => v.length, d => d[state.borders])
            let map = Object.fromEntries(geo_groups)
            return Object.keys(map).map(item => ({geography: item, value: map[item]}))
        },
        gender(state, getters) {
            let groupby_gender_age = rollups(getters.filteredData,
                v => v.length,
                d => d.age_group, d => d.Id10019)
            return groupby_gender_age.map(gender => ({age_group: gender[0], ...Object.fromEntries(gender[1])}))
        },
        placeOfDeath(state, getters) {
            let grouped = rollups(getters.filteredData, v => v.length, d => d.Id10058)
            return grouped
                .map(item => ({place: item[0].slice(0,15), value: item[1]}))
                .sort((a, b) => b.value - a.value)
        },
        topCauses(state, getters) {
            let grouped = rollup(getters.filteredData, v => v.length, d => d.cause)
            let map = Object.fromEntries(grouped)
            return Object.keys(map)
                .map(item => ({cause: item.slice(0, 15), value: map[item]}))
                .sort((a, b) => b.value - a.value)
        },
        ageGroup(state, getters) {
            let grouped = rollup(getters.filteredData, v => v.length, d => d.age_group)
            let map = Object.fromEntries(grouped)
            return Object.keys(map).map(item => ({name: item, value: map[item]}))
        },
        allCausesTrend(state, getters) {
            let dates = getters.filteredData.map(item => ({date: timeMonth(new Date(item.date)).toLocaleDateString()}))
            let grouped = rollup(dates, v => v.length, d => d.date)
            let map = Object.fromEntries(grouped)
            return Object.keys(map)
                .map(item => ({date: item, value: map[item]}))
                .sort((a, b) => new Date(a.date) - new Date(b.date))
        }
    },
    mutations: {
        changeBorders(state, typeOfBorder) {
            state.borders = typeOfBorder.toLowerCase()
        },
        resetAllDataToActive(state) {
            state.rawdata = state.rawdata.map(item => ({...item, active: true}))
        },
        filterByCauseOfDeath(state, COD) {
            if (COD) {
                state.rawdata = state.rawdata.map(item => ({
                    ...item,
                    active: item.cause === COD
                }))
            } else {
                state.rawdata = state.rawdata.map(item => ({...item, active: true}))
            }
        },
        filterByDate(state, startDate) {
            state.rawdata = state.rawdata.map(item => ({
                ...item,
                active: new Date(startDate) < new Date(item.date)
            }))
        },
        filterByDistrict(state, {district, province}) {
            if (district || province) {
                state.rawdata = state.rawdata.map(item => ({
                    ...item,
                    active: item.district.includes(district) || item.province === `${province} Province`
                }))
            } else {
                state.rawdata = state.rawdata.map(item => ({...item, active: true}))
            }

        },
    },
    actions: {
        async loadData({state}) {

            // TODO this request will fail because no session info is attached to request so will assume anonymousUser
            // const res = await axios.get('http://localhost:8000/va_analytics/api/dashboard')

            await axios.get('va_explorer_data.json')
                .then(res => {
                    state.rawdata = res.data.data.valid.map(item => ({...item, active: true}))
                    state.invalid = res.data.data.invalid
                })
                .catch(err => console.log(`Error retrieving data: ${err}`))
        }
    },
})
